# -*- coding: utf-8 -*-
"""字幕翻譯：把 SRT 翻成另一種語言，輸出一樣是 SRT（時間軸不變）

用 Google 的 MADLAD-400 3B（Apache 2.0）在本機翻譯，跟語音辨識共用 CTranslate2 引擎，
不會把字幕送到外部服務。

選這個模型的原因（實測比較過）：
- NLLB-200 的詞彙表缺很多中文字（例如「鋒」），中日韓譯文會出現 ⁇
- M2M100 雖然中文正常，但日文仍有缺字、韓文會誤譯
- MADLAD 譯文最自然、完全沒有缺字，代價是模型比較大（約 2.8 GB，第一次使用時下載）
"""
import os
import re
import threading
from pathlib import Path

import stt

MODEL_REPO = "Nextcloud-AI/madlad400-3b-mt-ct2-int8"
MODEL_FILES = ["model.bin", "config.json", "spiece.model", "shared_vocabulary.json"]
MODEL_SIZE_TEXT = "約 2.8 GB"
BATCH = 12

# code 跟語音辨識的語言代碼一致；madlad 是模型的目標語言標記；convert 是 OpenCC 的繁簡設定
TARGETS = [
    {"code": "zh-TW", "name": "繁體中文", "madlad": "zh", "convert": "s2twp"},
    {"code": "zh-CN", "name": "簡體中文", "madlad": "zh", "convert": "t2s"},
    {"code": "en", "name": "英文", "madlad": "en", "convert": None},
    {"code": "vi", "name": "越南語", "madlad": "vi", "convert": None},
    {"code": "ja", "name": "日語", "madlad": "ja", "convert": None},
    {"code": "ko", "name": "韓語", "madlad": "ko", "convert": None},
    {"code": "id", "name": "印尼語", "madlad": "id", "convert": None},
]

_lock = threading.Lock()
_model = None


class Cancelled(Exception):
    pass


def target(code):
    for t in TARGETS:
        if t["code"] == code:
            return t
    return None


def available():
    try:
        import ctranslate2  # noqa: F401
        import sentencepiece  # noqa: F401
        return True
    except ImportError:
        return False


def _cache_dir():
    return Path(stt.model_dir()) / ("models--" + MODEL_REPO.replace("/", "--"))


def model_ready():
    """模型是否已經下載完整（決定要不要提示使用者第一次比較久）。"""
    snaps = _cache_dir() / "snapshots"
    try:
        return any((s / "model.bin").is_file() and (s / "spiece.model").is_file()
                   for s in snaps.iterdir())
    except OSError:
        return False


def load():
    """下載（第一次）並載入翻譯模型。"""
    global _model
    with _lock:
        if _model is None:
            import ctranslate2
            import sentencepiece as spm
            from huggingface_hub import snapshot_download
            path = snapshot_download(MODEL_REPO, cache_dir=stt.model_dir(),
                                     allow_patterns=MODEL_FILES)
            try:
                tr = ctranslate2.Translator(path, device="cpu", compute_type="int8")
            except (RuntimeError, MemoryError) as e:
                raise RuntimeError("翻譯模型載入失敗，可能是記憶體不足（建議至少 8 GB）：%s" % e)
            sp = spm.SentencePieceProcessor(model_file=os.path.join(path, "spiece.model"))
            _model = (tr, sp)
        return _model


def translate(texts, target_code, on_progress=None, should_cancel=None):
    """把一串文字翻成目標語言，回傳同樣長度的清單。"""
    t = target(target_code)
    if not t:
        raise ValueError("不支援的翻譯語言：%s" % target_code)
    tr, sp = load()
    out = []
    total = len(texts)
    for i in range(0, total, BATCH):
        if should_cancel and should_cancel():
            raise Cancelled()
        chunk = texts[i:i + BATCH]
        toks = [sp.encode("<2%s> %s" % (t["madlad"], x), out_type=str) for x in chunk]
        res = tr.translate_batch(toks, beam_size=2, max_decoding_length=256,
                                 repetition_penalty=1.1)
        for r in res:
            text = sp.decode(r.hypotheses[0]).strip()
            out.append(stt.convert_text(text, t["convert"]))
        if on_progress:
            on_progress(min((i + len(chunk)) / total, 1.0))
    return out


# ---------------------------------------------------------------- SRT

_TIME = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}")


def parse_srt(text):
    """回傳 [(時間軸那一行, 字幕文字), ...]。"""
    blocks = []
    for raw in re.split(r"\r?\n\s*\r?\n", text.strip()):
        lines = [l for l in raw.splitlines() if l.strip() != ""]
        idx = next((k for k, l in enumerate(lines) if _TIME.match(l)), None)
        if idx is None:
            continue
        body = " ".join(lines[idx + 1:]).strip()
        if body:
            blocks.append((lines[idx].strip(), body))
    return blocks


def write_srt(path, blocks):
    # 先寫暫存檔再改名，避免中途失敗留下不完整的字幕
    path = Path(path)
    part = path.with_name(path.name + ".part")
    try:
        with open(part, "w", encoding="utf-8-sig", newline="\n") as f:
            for n, (timing, body) in enumerate(blocks, 1):
                f.write("%d\n%s\n%s\n\n" % (n, timing, body))
        os.replace(part, path)
    finally:
        part.unlink(missing_ok=True)


def translate_srt(srt_path, target_code, bilingual=False, on_progress=None, should_cancel=None):
    """翻譯一個 SRT 檔，輸出到旁邊，例如「影片.srt」→「影片.英文.srt」。回傳新檔路徑。"""
    t = target(target_code)
    if not t:
        raise ValueError("不支援的翻譯語言：%s" % target_code)
    src = Path(srt_path)
    blocks = parse_srt(src.read_text(encoding="utf-8-sig"))
    if not blocks:
        raise RuntimeError("字幕檔是空的，沒有東西可以翻譯")
    texts = translate([b for _, b in blocks], target_code, on_progress, should_cancel)
    if bilingual:
        out_blocks = [(timing, orig + "\n" + tr) for (timing, orig), tr in zip(blocks, texts)]
        name = "%s.雙語(%s).srt" % (src.stem, t["name"])
    else:
        out_blocks = [(timing, tr) for (timing, _), tr in zip(blocks, texts)]
        name = "%s.%s.srt" % (src.stem, t["name"])
    out = src.with_name(name)
    write_srt(out, out_blocks)
    return str(out)
