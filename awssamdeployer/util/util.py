import os
import subprocess
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from shutil import rmtree

from pymonad import Just, List, Left


@dataclass(frozen=True)
class StackData:
    stack_name: str
    bucket: str
    bucket_prefix: str = None
    template_name: str = 'template.yaml'


class ChangeDir:
    def __init__(self, directory):
        self.directory = directory
        self.previous_path = sys.path[0]

    def __enter__(self):
        os.chdir(str(self.directory.resolve()))
        return self.directory

    def __exit__(self, type, value, traceback):
        os.chdir(self.previous_path)


def _get_lambda_path_from_root(lambda_dir: str):
    return Path(f'./{lambda_dir}')


def _print_and_exit_with_error_code_if_left(result) -> None:
    print(result.value) if type(result) == Left else [print(r) for r in result]
    if type(result) == Left:
        exit(1)


def execute_shell_command(command: str):
    subprocess.run([command], shell=True)
    return List(f'Ran command {command}')


def get_as_path(value):
    return Just(Path(value))


def remove_dir(directory: Path):
    try:
        rmtree(directory)
        return List(f'Deleted directory {directory}')
    except FileNotFoundError:
        return List(f'No delete needed for {directory} - does not exist')


def _find_all_new(condition, location: Path):
    return List(*[x for x in location.iterdir() if condition(x)])


find_all_non_hidden_files = partial(_find_all_new, lambda x: x.is_file() and not x.name.startswith('.'))
find_all_non_hidden_dirs = partial(_find_all_new, lambda x: x.is_dir() and not x.name.startswith('.'))
