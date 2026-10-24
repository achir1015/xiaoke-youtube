# -*- coding: utf-8 -*-
"""語音轉文字 → SRT 字幕

用 faster-whisper（CTranslate2）在本機辨識，不需要 GPU 也不需要 torch。
中文另外用 OpenCC 做繁簡轉換，確保「繁體」真的是繁體。
"""
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path

# 介面上提供的語言；whisper 是給辨識引擎的語言代碼，convert 是 OpenCC 的轉換設定
LANGUAGES = [
    {"code": "auto", "name": "自動偵測", "whisper": None, "convert": None},
    {"code": "zh-TW", "name": "繁體中文", "whisper": "zh", "convert": "s2twp"},
    {"code": "zh-CN", "name": "簡體中文", "whisper": "zh", "convert": "t2s"},
    {"code": "en", "name": "英文", "whisper": "en", "convert": None},
    {"code": "vi", "name": "越南語", "whisper": "vi", "convert": None},
    {"code": "ja", "name": "日語", "whisper": "ja", "convert": None},
    {"code": "ko", "name": "韓語", "whisper": "ko", "convert": None},
    {"code": "id", "name": "印尼語", "whisper": "id", "convert": None},
]

MODELS = [
    {"code": "tiny", "name": "最快（tiny · 約 75 MB）"},
    {"code": "base", "name": "快（base · 約 145 MB）"},
    {"code": "small", "name": "推薦（small · 約 484 MB）"},
    {"code": "medium", "name": "最準（medium · 約 1.5 GB）"},
]

DEFAULT_MODEL = "small"

_models = {}
_model_lock = threading.Lock()
_converters = {}
_model_dir = None


class Cancelled(Exception):
    pass


def available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def language(code):
    for lang in LANGUAGES:
        if lang["code"] == code:
            return lang
    return LANGUAGES[0]


def _candidate_dirs():
    env = os.environ.get("XK_WHISPER_DIR")
    if env:
        yield Path(env)
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            yield Path(local) / "xiaoke-youtube" / "whisper"
    yield Path.home() / ".cache" / "xiaoke-whisper"
    yield Path(tempfile.gettempdir()) / "xiaoke-whisper"


def model_dir():
    """模型存放位置；有些電腦的 ~/.cache 被權限鎖住，所以要逐個試到能寫為止。"""
    global _model_dir
    if _model_dir:
        return _model_dir
    last = None
    for path in _candidate_dirs():
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            _model_dir = str(path)
            return _model_dir
        except OSError as e:
            last = e
            continue
    raise RuntimeError("找不到可以存放語音模型的資料夾：%s" % last)


def _init_cache_env():
    """huggingface_hub 的快取與鎖檔預設在 ~/.cache，那裡可能沒有權限，
    所以在載入任何相關套件之前就把它們一起導到我們能寫的資料夾。"""
    try:
        root = model_dir()
    except (OSError, RuntimeError):
        return
    hf = os.path.join(root, "hf")
    try:
        os.makedirs(hf, exist_ok=True)
    except OSError:
        return
    os.environ.setdefault("HF_HOME", hf)
    os.environ.setdefault("HF_HUB_CACHE", os.path.join(hf, "hub"))
    os.environ.setdefault("HF_XET_CACHE", os.path.join(hf, "xet"))
    # Windows 沒開開發人員模式不能建符號連結，HF 會一直跳警告；不影響運作
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("XDG_CACHE_HOME", root)


_init_cache_env()


def load_model(size):
    """載入並快取模型；第一次會從網路下載。"""
    from faster_whisper import WhisperModel
    size = size if any(m["code"] == size for m in MODELS) else DEFAULT_MODEL
    with _model_lock:
        if size not in _models:
            _models[size] = WhisperModel(
                size, device="cpu", compute_type="int8", download_root=model_dir())
        return _models[size]


def model_ready(size):
    """模型是不是已經下載過了（決定要不要提示使用者第一次比較久）。"""
    try:
        root = Path(model_dir())
        if not root.is_dir():
            return False
        needle = "whisper-" + (size or DEFAULT_MODEL)
        return any(needle in p.name for p in root.iterdir())
    except OSError:
        return False
    except RuntimeError:
        return False


def ffmpeg_exe():
    folder = os.environ.get("XK_FFMPEG_DIR")
    if folder:
        exe = Path(folder) / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if exe.exists():
            return str(exe)
    return "ffmpeg"


def decode_audio(path, rate=16000):
    """自己用 ffmpeg 解碼成 16kHz 單聲道浮點陣列。

    faster-whisper 內建的解碼走 PyAV，新版 PyAV 拿掉了它用到的參數會直接壞掉；
    我們本來就依賴 ffmpeg，索性自己解碼，穩定也少一層相依。
    """
    import numpy as np
    cmd = [ffmpeg_exe(), "-nostdin", "-hide_banner", "-loglevel", "error",
           "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(rate), "-"]
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000      # CREATE_NO_WINDOW，不要閃出黑視窗
    proc = subprocess.run(cmd, capture_output=True, **kwargs)
    if proc.returncode != 0 or not proc.stdout:
        tail = (proc.stderr or b"").decode("utf-8", "ignore").strip().splitlines()
        raise RuntimeError("ffmpeg 解碼失敗：" + (tail[-1] if tail else "沒有音訊"))
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def convert_text(text, rule):
    if not rule or not text:
        return text
    try:
        import opencc
    except ImportError:
        return text
    if rule not in _converters:
        _converters[rule] = opencc.OpenCC(rule)
    return _converters[rule].convert(text)


def timestamp(seconds):
    if seconds is None or seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def srt_path_for(media_path):
    p = Path(media_path)
    return p.with_suffix(".srt")


def transcribe(media_path, lang_code="auto", model_size=DEFAULT_MODEL,
               on_progress=None, should_cancel=None):
    """把影片／音訊轉成 SRT，回傳產生的 .srt 路徑。"""
    if not available():
        raise RuntimeError("還沒安裝語音辨識套件（faster-whisper）")

    lang = language(lang_code)
    model = load_model(model_size)

    audio = decode_audio(media_path)
    segments, info = model.transcribe(
        audio,
        language=lang["whisper"],
        vad_filter=True,
        beam_size=1,
        condition_on_previous_text=False,
    )
    total = float(getattr(info, "duration", 0) or 0)

    out = srt_path_for(media_path)
    # 先寫暫存檔，完整成功才改名：中途出錯、取消或 App 被關掉時，
    # 才不會留下一個空的或不完整的 .srt 冒充成功（使用者真的遇過 0 位元組的字幕檔）
    part = out.with_name(out.name + ".part")
    count = 0
    try:
        with open(part, "w", encoding="utf-8-sig", newline="\n") as f:
            for seg in segments:
                if should_cancel and should_cancel():
                    raise Cancelled()
                text = clean(seg.text)
                if not text:
                    continue
                text = convert_text(text, lang["convert"])
                count += 1
                f.write("%d\n%s --> %s\n%s\n\n" % (
                    count, timestamp(seg.start), timestamp(seg.end), text))
                if on_progress and total > 0:
                    on_progress(min(seg.end / total, 1.0))
        if count == 0:
            raise RuntimeError("這段影片裡沒有辨識到語音")
        os.replace(part, out)
    finally:
        part.unlink(missing_ok=True)

    if on_progress:
        on_progress(1.0)
    return str(out)


def clean(text):
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def install_command():
    return ["faster-whisper", "opencc-python-reimplemented", "sentencepiece"]
