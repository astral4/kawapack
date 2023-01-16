from UnityPy import Environment
from UnityPy.classes import Object, Sprite, Texture2D, TextAsset, AudioClip, MonoBehaviour
from UnityPy.enums import ClassIDType as Obj
from pathlib import Path
from collections.abc import Iterable
import json
import bson
from Crypto.Cipher import AES
from fsb5 import FSB5
from warnings import warn


def get_target_path(obj: Object, output_dir: Path, container_dir: Path) -> Path:
    container_dir = Path(*container_dir.parts[1:])

    if isinstance(obj, MonoBehaviour) and (script := obj.m_Script):
        return output_dir / container_dir / script.read().name

    assert isinstance(obj.name, str)
    return output_dir / container_dir / obj.name


def check_pattern_match(test_str: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        if pattern in test_str:
            return True
    return False


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


def export(obj: Object, target_path: Path) -> None:
    match obj:
        case Sprite() | Texture2D():
            if (img := obj.image).width > 0:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(target_path.with_suffix(".png"))

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
            fsb = FSB5(obj.m_AudioData)
            assert len(fsb.samples) == 1
            target_path = target_path.with_suffix("." + fsb.get_sample_extension())

            try:
                # Audio clip conversion will fail if DLLs needed by fsb5
                # (libogg, libvorbis, libvorbisenc, libvorbisfile) cannot be found
                # or the CRC32 value associated with the file format is incorrect.
                sample = fsb.rebuild_sample(fsb.samples[0])
                write_bytes(sample, target_path)
            except:
                warn(f"Failed to save audio clip to {target_path}", RuntimeWarning)

        case MonoBehaviour():
            tree = obj.read_typetree()
            if not obj.name:
                return

            target_path = target_path.joinpath(obj.name).with_suffix(".json")

            # If MonoBehaviours have identical file paths, unique
            # file names are generated to prevent overwriting data.
            if target_path.is_file():
                target_path.rename(target_path.with_stem(target_path.stem + "_0"))
                target_path = target_path.with_stem(target_path.stem + "_1")
                index = 1
                while target_path.is_file():
                    index += 1
                    new_name = f"_{index}".join(target_path.stem.rsplit(f"_{index-1}", 1))
                    target_path = target_path.with_stem(new_name)

            write_object(tree, target_path)


def extract_from_env(env: Environment, output_dir: Path, path_patterns: Iterable[str] | None):
    for object in env.objects:
        if object.type in {Obj.Sprite, Obj.Texture2D, Obj.TextAsset, Obj.AudioClip, Obj.MonoBehaviour}:
            resource = object.read()
            if isinstance(resource, Object):
                container_dir = Path(resource.container).parent if resource.container else Path(env.path)
                target_path = get_target_path(resource, output_dir, container_dir)
                if (not path_patterns) or check_pattern_match(target_path.as_posix(), path_patterns):
                    export(resource, target_path)