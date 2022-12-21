import UnityPy
from pathlib import Path
from warnings import warn


def convert(env: UnityPy.Environment, output_dir: Path):
    texts = []
    audio = []
    gamedata = []

    for object in env.objects:
        match object.type.name:
            case "Sprite" | "Texture2D":
                resource = object.read()
                target_path = Path(output_dir, resource.name).with_suffix(".png")
                resource.image.save(target_path)
            case "TextAsset":
                texts.append(object.read())
            case "AudioClip":
                audio.append(object.read())
            case "MonoBehaviour":
                gamedata.append(object.read())
            case _:
                warn(f"Asset type '{object.type.name}' in the environment at '{env.path}' is not recognized.", RuntimeWarning)