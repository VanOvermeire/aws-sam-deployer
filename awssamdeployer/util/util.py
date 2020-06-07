import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree


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


def _find_all(location: Path, condition):
    return list([x for x in location.iterdir() if condition(x)])


def find_all_non_hidden_files(location: Path):
    return _find_all(location, lambda x: x.is_file() and not x.name.startswith('.'))


def find_all_non_hidden_dirs(location: Path):
    return _find_all(location, lambda x: x.is_dir() and not x.name.startswith('.'))


def execute_shell_commands(commands: list):
    # TODO capture_output and if error, stop processing?
    [subprocess.run([c], shell=True) for c in commands]


def remove_dir(directory: Path):
    try:
        rmtree(directory)
    except FileNotFoundError:
        pass
