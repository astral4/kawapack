from UnityPy import Environment
from UnityPy.classes import Sprite, Texture2D, TextAsset, AudioClip, MonoBehaviour
from pathlib import Path
import json
import bson
from Crypto.Cipher import AES

def write_bytes(data: bytes, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def write_object(data: object, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def write_binary_object(data: bytes, path: Path):
    try:
        decoded = bson.decode(data)
        write_object(decoded, path)
    except:
        # BSON decoding fails if data is JSON-encoded BSON instead of plain BSON
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

def convert_from_env(env: Environment, output_dir: Path):
    for object in env.objects:
        if object.type.name in {"Sprite", "Texture2D", "TextAsset", "AudioClip", "MonoBehaviour"}:
            resource = object.read()

            if isinstance(resource, (Sprite, Texture2D)):
                target_path = output_dir.joinpath(env.path, resource.name)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                resource.image.save(target_path.with_suffix(".png"))

            elif isinstance(resource, TextAsset):
                target_path = output_dir.joinpath(env.path, resource.name)
                target_path_str = target_path.as_posix()
                data = bytes(resource.script)

                if "gamedata/story" in target_path_str:
                    # Story text is unencrypted, so the data can be directly written
                    write_bytes(data, target_path)
                elif "gamedata/levels/" in target_path_str:
                    data = decrypt_textasset(data, 0)
                    write_binary_object(data, target_path)
                else:
                    try:
                        data = decrypt_textasset(data)
                        write_binary_object(data, target_path)
                    except:
                        # Decryption will fail if the data is not actually encrypted
                        write_bytes(data, target_path)
            
            elif isinstance(resource, AudioClip):
                target_path = output_dir.joinpath(env.path, resource.name)
                for audio_name, audio_data in resource.samples.items():
                    write_bytes(audio_data, target_path.joinpath(audio_name).with_suffix(".wav"))
            
            elif isinstance(resource, MonoBehaviour):
                target_path = output_dir.joinpath(env.path, resource.name)
                tree = resource.read_typetree()
                if not tree["m_Name"] or tree["m_Name"].isspace():
                    target_path = Path(output_dir, str(resource.path_id))
                write_object(tree, target_path)