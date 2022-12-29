from UnityPy import Environment
from UnityPy.classes import Sprite, Texture2D, TextAsset, AudioClip, MonoBehaviour
from pathlib import Path
import json

def write_bytes(data: bytes, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def write_object(data: object, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def convert_from_env(env: Environment, output_dir: Path):
    for object in env.objects:
        if object.type.name in {"Sprite", "Texture2D", "TextAsset", "AudioClip", "MonoBehaviour"}:
            resource = object.read()

            if isinstance(resource, (Sprite, Texture2D)):
                target_path = Path(output_dir, env.path, resource.name)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                resource.image.save(target_path.with_suffix(".png"))

            if isinstance(resource, TextAsset):
                target_path = Path(output_dir, env.path, resource.name)
                write_bytes(bytes(resource.script), target_path)
            
            if isinstance(resource, AudioClip):
                target_path = Path(output_dir, env.path, resource.name)
                write_bytes(b"".join(resource.samples.values()), target_path.with_suffix(".wav"))
            
            if isinstance(resource, MonoBehaviour):
                target_path = Path(output_dir, env.path, resource.name)
                tree = resource.read_typetree()
                if not tree["m_Name"] or tree["m_Name"].isspace():
                    target_path = Path(output_dir, str(resource.path_id))
                write_object(tree, target_path)