from pathlib import Path
from shutil import rmtree
from warnings import warn
import UnityPy
from .convert_ab import convert_from_env
from .combine import combine

def convert(input_dir: Path, output_dir: Path, overwrite: bool = True, show_warnings: bool = True):
    if not (input_dir.exists() and input_dir.is_dir()):
        warn("The input directory does not exist.", RuntimeWarning)
        return
    if not overwrite and output_dir.exists() and output_dir.is_dir():
        warn("The output directory already exists, and the overwrite setting is set to False.", RuntimeWarning)
        return

    if output_dir.is_dir():
        rmtree(output_dir)
    output_dir.mkdir()

    for path in input_dir.glob("**/*.ab"):
        if path.is_file():
            environment = UnityPy.load(path.as_posix())
            if len(environment.objects) > 0:
                convert_from_env(environment, output_dir, show_warnings)

    combine_textures(output_dir)

def combine_textures(input_dir: Path):
    for alpha_path in input_dir.glob("**/*_alpha.png"):
        if (rgb_path := alpha_path.with_name(alpha_path.name[:-10]).with_suffix(".png")).exists():
            target_path = rgb_path.with_name(
                rgb_path.name.split("-")[1]
            )
            combine(rgb_path, alpha_path, target_path.with_suffix(".png"))