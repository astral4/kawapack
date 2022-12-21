import UnityPy
from warnings import warn

def convert(env: UnityPy.Environment):
    sprites = []
    textures = []
    texts = []
    audio = []
    gamedata = []

    for object in env.objects:
        match object.type.name:
            case "Sprite":
                sprites.append(object.read())
            case "Texture2D":
                textures.append(object.read())
            case "TextAsset":
                texts.append(object.read())
            case "AudioClip":
                audio.append(object.read())
            case "MonoBehaviour":
                gamedata.append(object.read())
            case _:
                warn(f"Asset type '{object.type.name}' is not recognized.", RuntimeWarning)