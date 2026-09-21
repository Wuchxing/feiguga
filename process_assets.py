"""将原始浅色背景素材转换为适合桌宠使用的小尺寸透明 PNG。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets"
OUTPUT = ROOT / "assets_processed"
FILES = [
    "01-core-standard.png", "02-pose-sit.png", "03-pose-wave.png",
    "04-pose-eat.png", "05-pose-roll.png", "06-exp-sleepy.png",
    "07-exp-cry.png", "08-exp-angry.png", "09-exp-happy.png",
]


def remove_background(source: Path, destination: Path) -> None:
    # 先缩小再抠图，显著减少运行时内存，同时保留桌宠显示所需的细节。
    image = Image.open(source).convert("RGB")
    image.thumbnail((512, 512), Image.Resampling.LANCZOS)

    # 素材背景均为从画布边缘连通的浅灰色。Pillow 的洪水填充只移除
    # 边缘连通区域，因此角色自身的白肚皮、眼白不会被误删。
    background = image.copy()
    draw = ImageDraw.Draw(background)
    seeds = [(0, 0), (image.width - 1, 0), (0, image.height - 1),
             (image.width - 1, image.height - 1)]
    for seed in seeds:
        ImageDraw.floodfill(background, seed, (255, 0, 255), thresh=42)

    marker = background.load()
    alpha = Image.new("L", image.size, 255)
    alpha_pixels = alpha.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = marker[x, y]
            if r > 245 and b > 245 and g < 20:
                alpha_pixels[x, y] = 0

    # 轻微扩张再羽化，避免白色背景边缘和锯齿。
    alpha = alpha.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    result = image.convert("RGBA")
    result.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        result = result.crop(bbox)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, optimize=True)


def main() -> None:
    for name in FILES:
        print(f"处理 {name}")
        remove_background(SOURCE / name, OUTPUT / name)
    print(f"完成：{OUTPUT}")


if __name__ == "__main__":
    main()
