import UnityPy
from pathlib import Path
from warnings import warn


def write_bytes(data: bytes, path: Path):
    path.mkdir()
    with open(path, "wb") as f:
        f.write(data)


def convert(env: UnityPy.Environment, output_dir: Path):
    for object in env.objects:
        resource = object.read()
        if hasattr(resource, "name"):
            target_path = Path(output_dir, resource.name)
        match object.type.name:
            case "Sprite" | "Texture2D":
                resource.image.save(target_path.with_suffix(".png"))
            case "TextAsset":
                write_bytes(bytes(resource.script), target_path)
            case "AudioClip":
                write_bytes(bytes.join(resource.samples.items()), target_path)
            case "MonoBehaviour":
                warn(f"Not implemented yet", RuntimeWarning)
            case _:
                warn(f"Asset type '{object.type.name}' at '{env.path}' is not recognized.", RuntimeWarning)