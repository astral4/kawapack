from os import PathLike
from collections.abc import Iterable
from pathlib import Path
from shutil import rmtree
from warnings import warn
from UnityPy import Environment
from PIL import Image
from .convert_ab import convert_from_env


DirPath = str | PathLike[str]


def convert(input_dir: DirPath, output_dir: DirPath, path_patterns: Iterable[str] | None = None, show_logs: bool = True, reset: bool = True):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not (input_dir.exists() and input_dir.is_dir()):
        warn("The input directory does not exist.", RuntimeWarning)
        return

    if reset and output_dir.is_dir():
        rmtree(output_dir)
    
    output_dir.mkdir()

    for path in input_dir.glob("**/*.ab"):
        if path.is_file():
            env = Environment(path.as_posix())
            convert_from_env(env, output_dir, path_patterns, show_logs)

    combine_textures(output_dir)


def combine_textures(input_dir: Path):
    for alpha_path in input_dir.glob("**/*alpha*.png"):
        rgb_path = None
        if alpha_path.stem.endswith("_alpha"):
            rgb_path = alpha_path.with_stem(alpha_path.stem[:-6])
        elif alpha_path.stem.endswith("[alpha]"):
            rgb_path = alpha_path.with_stem(alpha_path.stem[:-7])

        if rgb_path and rgb_path.exists():
            rgb_image = Image.open(rgb_path).convert("RGBA")
            alpha_image = Image.open(alpha_path).convert("L")

            # RGB and alpha layers should have the same dimensions.
            # If not, the image data is assumed to be invalid.
            if rgb_image.size == alpha_image.size:
                rgb_image.putalpha(alpha_image)
                rgb_image.save(rgb_path)
            else:
                rgb_path.unlink()

            alpha_path.unlink()