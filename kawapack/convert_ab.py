import UnityPy
from pathlib import Path
from PIL import Image
import json

def write_bytes(data: bytes, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def write_object(data: object, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)                        

def convert_from_env(env: UnityPy.Environment, output_dir: Path):
    for object in env.objects:
        if object.type.name in {"Sprite", "Texture2D", "TextAsset", "AudioClip", "MonoBehaviour", "AssetBundle"}:
            resource = object.read()
            if hasattr(resource, "name"):
                target_path = Path(output_dir, env.path, resource.name)

            match object.type.name:
                case "Sprite" | "Texture2D":
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    resource.image.save(target_path.with_suffix(".png"))
                case "TextAsset":
                    write_bytes(bytes(resource.script), target_path)
                case "AudioClip":
                    write_bytes(b"".join(resource.samples.items()), target_path.with_suffix(".wav"))
                case "MonoBehaviour":
                    if resource.serialized_type.nodes:
                        tree = resource.read_typetree()
                        if not tree["m_Name"] or tree["m_Name"].isspace():
                            target_path = Path(output_dir, str(resource.path_id))
                        write_object(tree, target_path)
                case "AssetBundle":
                    if resource.serialized_type.nodes:
                        tree = resource.read_typetree()
                        write_object(tree, target_path)