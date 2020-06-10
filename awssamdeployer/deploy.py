from pathlib import Path
from shutil import copytree

from pymonad import Left, Right, Just, List

from awssamdeployer.util.checks import check_requirements
from awssamdeployer.util.constants import COMMON_DIRECTORY, DIST, DEFAULT_DIR
from awssamdeployer.util.util import StackData, ChangeDir, remove_dir, find_all_non_hidden_dirs, execute_shell_command, get_as_path, find_all_non_hidden_files, _print_and_exit_with_error_code_if_left


def _requires_pip_install(directory: Path):
    return 'requirements.txt' in [x.name for x in find_all_non_hidden_files(directory.absolute())]


def _run_pip_install(directory: Path):
    if _requires_pip_install(directory):
        with ChangeDir(directory):
            print(f'Running pip install in {directory}')
            execute_shell_command('pip3 install -r requirements.txt -t . >> /dev/null')
    return Just(directory)


def _get_dist_path(directory: Path):
    return Path(f'{directory.absolute()}/{DIST}')


def _remove_dist(directory: Path):
    dist_path = _get_dist_path(directory)
    return remove_dir(dist_path)


def _run_zip(directory: Path):
    with ChangeDir(directory):
        zip_name = f'{directory.parent.name}.zip'
        execute_shell_command(f'zip -r {zip_name} . >> /dev/null')
    return Just(directory)


def _create_dist_and_copy_files(directory: Path):
    dist_path = _get_dist_path(directory)
    copytree(directory, dist_path)
    return Just(dist_path)


def _ignore_common(directory: Path):
    return Left(f'Ignoring {COMMON_DIRECTORY}: {directory}') if COMMON_DIRECTORY in directory.name else Right(directory)


def _create_zip(directory: Path):
    result = _ignore_common(directory) >> _create_dist_and_copy_files >> _run_pip_install >> _run_zip
    return List(result.value) if type(result) == Left else List(f'Created zip for {result.value}')


def _build_stack_commands(stack_data: StackData, prefix):
    # TODO could do check: if path of codeuri refers to something local, use this.
    #   else use python commands: create_change_set -> wait -> execute_change_set
    return List(f'aws cloudformation package --template-file {stack_data.template_name} --s3-bucket "{stack_data.bucket}" --s3-prefix "{prefix}" --output-template-file outputSamTemplate.yaml',
                f'aws cloudformation deploy --template-file outputSamTemplate.yaml --stack-name {stack_data.stack_name} --capabilities CAPABILITY_IAM',
                'rm outputSamTemplate.yaml')  # use path for this?


def remove_dists(lambda_dir: str = DEFAULT_DIR):
    result = check_requirements(lambda_dir) >> get_as_path >> find_all_non_hidden_dirs >> _remove_dist
    _print_and_exit_with_error_code_if_left(result)


def create_zips(lambda_dir: str = DEFAULT_DIR):
    dirs = check_requirements(lambda_dir) >> get_as_path >> find_all_non_hidden_dirs
    removes = dirs >> _remove_dist
    zips = dirs >> _create_zip
    _print_and_exit_with_error_code_if_left(removes + zips)


def create_stack(stack_data: StackData) -> None:
    prefix = stack_data.bucket_prefix if stack_data.bucket_prefix else stack_data.stack_name
    result = _build_stack_commands(stack_data, prefix) >> execute_shell_command
    _print_and_exit_with_error_code_if_left(result)


def deploy(stack_data: StackData, lambda_dir: str = DEFAULT_DIR) -> None:
    create_zips(lambda_dir)
    create_stack(stack_data)
    remove_dists(lambda_dir)
