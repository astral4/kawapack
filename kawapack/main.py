from os import PathLike
from collections.abc import Iterable
from pathlib import Path
from shutil import rmtree
from warnings import warn
from UnityPy import Environment
from PIL import Image
import json
from typing import Any
from .extract_ab import extract_from_env


DirPath = str | PathLike[str]


def extract_all(
    input_dir: DirPath,
    output_dir: DirPath,
    path_patterns: Iterable[str] | None = None,
    reset: bool = True,
    portrait_dir: DirPath | None = None
) -> None:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        warn("The input directory does not exist.", RuntimeWarning)
        return

    if reset and output_dir.is_dir():
        rmtree(output_dir)
    
    output_dir.mkdir()

    for path in input_dir.glob("**/*.ab"):
        if path.is_file():
            env = Environment(path.as_posix())
            extract_from_env(env, output_dir, path_patterns)

    combine_textures(output_dir)

    if portrait_dir:
        if (portrait_dir := Path(portrait_dir)).is_dir():
            portrait_dir = Path(output_dir, *portrait_dir.parts[1:])
            data_dir = output_dir / "torappu" / "dynamicassets" / "arts" / "charportraits" / "UIAtlasTextureRef"
            process_portraits(portrait_dir, data_dir)
        else:
            warn("A portrait directory was specified, but it does not exist.", RuntimeWarning)


def get_rgb_path(alpha_path: Path, alpha_suffixes: Iterable[str]) -> Path | None:
    for suffix in alpha_suffixes:
        if alpha_path.stem.endswith(suffix):
            return alpha_path.with_stem(alpha_path.stem[:-len(suffix)])
        

def merge_rgba(rgb_path: Path, alpha_path: Path) -> None:
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


def combine_textures(input_dir: Path) -> None:
    ALPHA_SUFFIXES = ("_alpha", "[alpha]", "a")

    for alpha_path in input_dir.glob("**/*.png"):
        if alpha_path.stem.endswith(ALPHA_SUFFIXES):
            rgb_path = get_rgb_path(alpha_path, ALPHA_SUFFIXES)
            if rgb_path and rgb_path.is_file():
                merge_rgba(rgb_path, alpha_path)


def extract_portraits_from_image(image_path: Path, sprite_data: list[dict[str, Any]], output_dir: Path) -> None:
    image = Image.open(image_path)

    for sprite in sprite_data:
        rect = sprite["rect"]
        portrait = image.crop((
            rect["x"],
            image.height - (rect["y"] + rect["h"]),
            rect["x"] + rect["w"],
            image.height - rect["y"]
        ))
        if sprite["rotate"]:
            portrait = portrait.transpose(method=Image.ROTATE_270)

        target_path = Path(output_dir, sprite["name"]).with_suffix(".png")
        portrait.save(target_path)

    image_path.unlink()


def process_portraits(image_dir: Path, data_dir: Path) -> None:
    for data_path in data_dir.glob("*.json"):
        with open(data_path, "r") as f:
            portrait_data = json.load(f)
        image_name = portrait_data["m_Name"]
        sprites = portrait_data["_sprites"]

        image_path = Path(image_dir, image_name).with_suffix(".png")
        if image_path.is_file():
            extract_portraits_from_image(image_path, sprites, image_dir)