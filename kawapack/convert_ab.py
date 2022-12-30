from UnityPy import Environment
from UnityPy.classes import Object, Sprite, Texture2D, TextAsset, AudioClip, MonoBehaviour
from pathlib import Path
import json
import bson
from Crypto.Cipher import AES


def get_target_path(obj: Object, output_dir: Path, container_dir: Path) -> Path:
    if isinstance(obj, MonoBehaviour):
        return output_dir / container_dir / obj.m_Script.read().name

    assert isinstance(obj.name, str)
    return output_dir / container_dir / obj.name


def write_bytes(data: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def write_object(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def write_binary_object(data: bytes, path: Path) -> None:
    try:
        # BSON decoding fails if data is JSON-encoded BSON instead of plain BSON
        decoded = bson.decode(data)
        write_object(decoded, path)
    except:
        write_object(json.loads(data), path)


def decrypt_textasset(stream: bytes, start_index: int = 128) -> bytes:
    BITMASK = bytes.fromhex('554954704169383270484157776e7a7148524d4377506f6e4a4c49423357436c').decode()

    def unpad(data: bytes) -> bytes:
        end_index = len(data) - data[-1]
        return data[:end_index]

    data = stream[start_index:]

    aes_key = BITMASK[:16].encode()
    aes_iv = bytearray(
        buffer_bit ^ mask_bit
        for (buffer_bit, mask_bit) in zip(data[:16], BITMASK[16:].encode())
    )

    decrypted = (
        AES.new(aes_key, AES.MODE_CBC, aes_iv)
        .decrypt(data[16:])
    )

    return unpad(decrypted)


def export(obj: Object, output_dir: Path, container_dir: Path) -> None:
    target_path = get_target_path(obj, output_dir, container_dir)

    match obj:
        case Sprite() | Texture2D():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            obj.image.save(target_path.with_suffix(".png"))
        case TextAsset():
            target_path_str = target_path.as_posix()
            data = bytes(obj.script)
            if "gamedata/story" in target_path_str:
                # Story text is unencrypted, so the data can be directly written
                write_bytes(data, target_path.with_suffix(".txt"))
            elif "gamedata/levels/" in target_path_str:
                data = decrypt_textasset(data, 0)
                write_binary_object(data, target_path)
            else:
                try:
                    # Decryption will fail if the data is not actually encrypted
                    data = decrypt_textasset(data)
                    write_binary_object(data, target_path)
                except:
                    try:
                        write_object(json.loads(data), target_path)
                    except:
                        write_bytes(data, target_path)
        case AudioClip():
            for audio_name, audio_data in obj.samples.items():
                write_bytes(audio_data, target_path.joinpath(audio_name).with_suffix(".wav"))
        case MonoBehaviour():
            tree = obj.read_typetree()
            write_object(tree, target_path)


def convert_from_env(env: Environment, output_dir: Path):
    for object in env.objects:
        if object.type.name in {"Sprite", "Texture2D", "TextAsset", "AudioClip", "MonoBehaviour"}:
            resource = object.read()
            if isinstance(resource, Object):
                container_dir = Path(resource.container).parent if resource.container else Path(env.path)
                export(resource, output_dir, container_dir)
        else:
            print(f"{object.type.name} object at {env.path} was not processed")