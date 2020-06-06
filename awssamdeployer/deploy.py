import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

COMMON_DIRECTORY = 'common'


class ChangeDir:
    def __init__(self, directory):
        self.directory = directory
        self.previous_path = sys.path[0]

    def __enter__(self):
        os.chdir(str(self.directory.resolve()))
        return self.directory

    def __exit__(self, type, value, traceback):
        os.chdir(self.previous_path)


@dataclass(frozen=True)
class StackData:
    stack_name: str
    bucket: str
    bucket_prefix: str = None
    template_name: str = 'template.yaml'


def _find_all(location: str, condition):
    return list([x for x in Path(location).iterdir() if condition(x)])


def _find_all_non_hidden_files(location: str):
    return _find_all(location, lambda x: x.is_file() and not x.name.startswith('.'))


def _find_all_non_hidden_dirs(location: str):
    return _find_all(location, lambda x: x.is_dir() and not x.name.startswith('.'))


def _find_all_non_hidden_files_and_dirs(location: str):
    return _find_all(location, lambda x: not x.name.startswith('.'))


def _execute_shell_commands(commands: list):
    [subprocess.run([c], shell=True) for c in commands]


def _requires_pip_install(directory: Path):
    return 'requirements.txt' in [x.name for x in _find_all_non_hidden_files(directory.relative_to('.'))]


def _run_pip_install(directory: Path):
    with ChangeDir(directory):
        print(f'Running pip install for directory {directory}')
        _execute_shell_commands(['pip3 install -r requirements.txt -t . >> /dev/null'])


def _run_zip(directory: Path):
    with ChangeDir(directory):
        print(f'Creating zip for directory {directory}')
        zip_name = f'{directory.name}.zip'
        _execute_shell_commands([
            'rm -rf ./dist',
            f'zip -r {zip_name} . >> /dev/null',
            'mkdir dist',
            f'mv {zip_name} dist',
        ])


def _check_if_requirements_ok(lambda_dir: str):
    dirs = _find_all_non_hidden_dirs('.')
    dir_names = [d.name for d in dirs]

    if lambda_dir not in dir_names:
        this_dir = Path('.').absolute()
        print(f'Did not find a "{lambda_dir}" directory in {this_dir}. Note: create_zips should be run from the root of your project')
        return False
    dirs = _find_all_non_hidden_dirs(f'./{lambda_dir}')

    if len(dirs) == 0:
        print(f'Directory {lambda_dir} seems to be empty')
        return False

    for d in dirs:
        file_names = [x.name for x in _find_all_non_hidden_files(d)]
        any_python_files = any([x.endswith('.py') for x in file_names])

        if not any_python_files:
            print(f'Could not find python files in {d}')
            return False
    return True


def _remove_dist(location: Path):
    with ChangeDir(location):
        print(f'Removing any dist folders in {location}')
        _execute_shell_commands(['rm -rf ./dist'])


def remove_dists(lambda_dir: str = 'lambdas') -> None:
    if _check_if_requirements_ok(lambda_dir):
        for d in _find_all_non_hidden_dirs(f'./{lambda_dir}'):
            _remove_dist(d)


def create_zips(lambda_dir: str = 'lambdas'):
    if _check_if_requirements_ok(lambda_dir):
        for d in _find_all_non_hidden_dirs(f'./{lambda_dir}'):
            if COMMON_DIRECTORY in d.name:
                print(f'Ignoring common module {d}')
            else:
                if _requires_pip_install(d):
                    _run_pip_install(d)
                _run_zip(d)


def create_stack(stack_data: StackData) -> None:
    prefix = stack_data.bucket_prefix if stack_data.bucket_prefix else stack_data.stack_name
    _execute_shell_commands([
        f'aws cloudformation package --template-file {stack_data.template_name} --s3-bucket "{stack_data.bucket}" --s3-prefix "{prefix}" --output-template-file outputSamTemplate.yaml',
        f'aws cloudformation deploy --template-file outputSamTemplate.yaml --stack-name {stack_data.stack_name} --capabilities CAPABILITY_IAM',
        'rm outputSamTemplate.yaml',
    ])


def deploy(stack_data: StackData, lambda_dir: str = 'lambdas') -> None:
    create_zips(lambda_dir)
    create_stack(stack_data)
    remove_dists(lambda_dir)
