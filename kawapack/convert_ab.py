import UnityPy
from pathlib import Path
import json
from warnings import warn


def write_bytes(data: bytes, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
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
                write_bytes(bytes.join(resource.samples.items()), target_path.with_suffix(".wav"))
            case "MonoBehaviour":
                if resource.serialized_type.nodes:
                    tree = resource.read_typetree()
                    if tree["m_Name"] and not tree["m_Name"].isspace():
                        target_path = Path(target_path, tree["m_Name"])
                    else:
                        target_path = Path(output_dir, str(resource.path_id))
                    
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path.with_suffix(".json"), "w", encoding="utf8") as f:
                        json.dump(tree, f, ensure_ascii=False, indent=4)
                else:
                    warn(f"MonoBehaviour at '{env.path}' did not have any nodes to serialize", RuntimeWarning)
            case _:
                warn(f"Asset type '{object.type.name}' at '{env.path}' is not recognized.", RuntimeWarning)