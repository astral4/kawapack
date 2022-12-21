from pathlib import Path
from PIL import Image

def combine(path_rgb: Path, path_a: Path, target_path: Path):
    rgb_image = Image.open(path_rgb).convert("RGBA")
    alpha_image = Image.open(path_a).convert("L")

    rgb_image.putalpha(alpha_image)
    rgb_image.save(target_path)

    path_rgb.unlink()
    path_a.unlink()
