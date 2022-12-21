from pathlib import Path
from shutil import rmtree
from warnings import warn
import UnityPy
from convert_ab import convert

def main(input_dir: str, output_dir: str, overwrite: bool = True):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not (input_path.exists() and input_path.is_dir()):
        warn("The input directory does not exist.", RuntimeWarning)
        return
    if not overwrite and output_path.exists() and output_path.is_dir():
        warn("The output directory already exists, and the overwrite setting is set to False.", RuntimeWarning)
        return

    if output_path.is_dir():
        rmtree(output_path)
    output_path.mkdir()

    for path in input_path.glob("**/*.ab"):
        if path.is_file():
            environment = UnityPy.load(path.as_posix())
            if len(environment.objects) > 0:
                convert(environment, output_dir)