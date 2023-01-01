from os import PathLike
from collections.abc import Iterable
from pathlib import Path
from shutil import rmtree
from warnings import warn
from UnityPy import Environment
from PIL import Image
from .convert_ab import convert_from_env


FilePath = str | PathLike[str]


def convert(input_dir: FilePath, output_dir: FilePath, path_start_patterns: Iterable[str], reset: bool = True):
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
            convert_from_env(env, output_dir, path_start_patterns)

    combine_textures(output_dir)


def combine_textures(input_dir: Path):
    for alpha_path in input_dir.glob("**/*_alpha.png"):
        if (rgb_path := alpha_path.with_name(alpha_path.name[:-10]).with_suffix(".png")).exists():
            target_path = (
                rgb_path
                .with_name(rgb_path.name.split("-")[1])
                .with_suffix(".png")
            )

            rgb_image = Image.open(rgb_path).convert("RGBA")
            alpha_image = Image.open(alpha_path).convert("L")

            rgb_image.putalpha(alpha_image)
            rgb_image.save(target_path)

            rgb_path.unlink()
            alpha_path.unlink()