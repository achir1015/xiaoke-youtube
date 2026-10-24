# -*- coding: utf-8 -*-
"""產生小柯機器人 YouTube 下載工具的各尺寸圖示。

用法： python tools/make_icons.py
輸出： web/favicon.ico、web/favicon-32.png、web/icon-180.png、
       web/icon-192.png、web/icon-512.png、web/icon-512-maskable.png
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
EXT_ICONS = ROOT / "extension" / "icons"
ANDROID_RES = ROOT / "android" / "app" / "src" / "main" / "res"
S = 1024  # 先畫大圖再縮，邊緣才漂亮


def vgrad(size, top, bottom):
    img = Image.new("RGB", (1, size[1]))
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        img.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize(size)


def draw_icon(pad_ratio=0.0, bg=None):
    """pad_ratio > 0 時留白（maskable 用），bg 為底色。"""
    img = Image.new("RGBA", (S, S), bg or (0, 0, 0, 0))
    inner = int(S * (1 - pad_ratio * 2))
    art = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(art)
    u = S / 64.0  # 以 64 格座標作圖，跟 icon.svg 一致

    def R(*v):
        return [x * u for x in v]

    # 天線
    d.line(R(32, 6, 32, 12), fill=(143, 166, 189), width=int(3 * u))
    d.ellipse(R(28.5, 2, 35.5, 9), fill=(56, 189, 248))

    # 頭盔（上亮下暗的漸層）
    helm_box = (int(8 * u), int(10 * u), int(56 * u), int(50 * u))
    w, h = helm_box[2] - helm_box[0], helm_box[3] - helm_box[1]
    grad = vgrad((w, h), (160, 183, 206), (84, 107, 130)).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=int(12 * u), fill=255)
    art.paste(grad, helm_box[:2], mask)

    d = ImageDraw.Draw(art)
    # 耳機
    d.rounded_rectangle(R(2, 24, 9, 39), radius=int(3.5 * u), fill=(68, 88, 110))
    d.rounded_rectangle(R(55, 24, 62, 39), radius=int(3.5 * u), fill=(68, 88, 110))
    # 面罩
    d.rounded_rectangle(R(14, 19, 50, 41), radius=int(9 * u), fill=(16, 23, 34))
    # 眼睛
    d.ellipse(R(20, 26, 28, 34), fill=(56, 189, 248))
    d.ellipse(R(36, 26, 44, 34), fill=(56, 189, 248))
    d.ellipse(R(22, 28, 25.5, 31.5), fill=(190, 240, 255))
    d.ellipse(R(38, 28, 41.5, 31.5), fill=(190, 240, 255))
    # YouTube 播放徽章
    d.rounded_rectangle(R(31, 40, 61, 61), radius=int(6.5 * u), fill=(255, 59, 48))
    d.polygon(R(42, 44.5, 42, 56.5, 52, 50.5), fill=(255, 255, 255))

    if pad_ratio > 0:
        art = art.resize((inner, inner), Image.LANCZOS)
        off = (S - inner) // 2
        img.alpha_composite(art, (off, off))
    else:
        img.alpha_composite(art)
    return img


def main():
    base = draw_icon()
    for size, name in [(512, "icon-512.png"), (192, "icon-192.png"),
                       (180, "icon-180.png"), (32, "favicon-32.png")]:
        base.resize((size, size), Image.LANCZOS).save(WEB / name)

    mask = draw_icon(pad_ratio=0.12, bg=(13, 17, 23, 255))
    mask.resize((512, 512), Image.LANCZOS).save(WEB / "icon-512-maskable.png")

    base.resize((256, 256), Image.LANCZOS).save(
        WEB / "favicon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])

    # 瀏覽器擴充功能用的圖示
    EXT_ICONS.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 48, 128):
        base.resize((size, size), Image.LANCZOS).save(EXT_ICONS / ("icon-%d.png" % size))

    # Android：傳統方形圖示 + 自適應圖示的前景層
    densities = [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
                 ("xxhdpi", 144), ("xxxhdpi", 192)]
    for name, size in densities:
        folder = ANDROID_RES / ("mipmap-" + name)
        folder.mkdir(parents=True, exist_ok=True)
        icon = base.resize((size, size), Image.LANCZOS)
        icon.save(folder / "ic_launcher.png")
        icon.save(folder / "ic_launcher_round.png")

    # 自適應圖示的前景要留安全邊距，不然圓形遮罩會把機器人切到
    fg = draw_icon(pad_ratio=0.18)
    fg_dir = ANDROID_RES / "drawable"
    fg_dir.mkdir(parents=True, exist_ok=True)
    fg.resize((432, 432), Image.LANCZOS).save(fg_dir / "ic_launcher_foreground.png")

    print("圖示已輸出到", WEB, "、", EXT_ICONS, "與", ANDROID_RES)


if __name__ == "__main__":
    main()
