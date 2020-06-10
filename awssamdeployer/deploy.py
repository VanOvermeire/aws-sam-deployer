from pathlib import Path
from shutil import copytree

from pymonad import Left, Right, Just, List

from awssamdeployer.util.constants import COMMON_DIRECTORY, DIST
from awssamdeployer.util.util import StackData, ChangeDir, remove_dir, find_all_non_hidden_dirs, execute_shell_command, get_as_path, find_all_non_hidden_files


def _requires_pip_install(directory: Path):
    return 'requirements.txt' in [x.name for x in find_all_non_hidden_files(directory.absolute())]


def _run_pip_install(directory: Path):
    with ChangeDir(directory):
        print(f'Running pip install in directory {directory}')
        execute_shell_command('pip3 install -r requirements.txt -t . >> /dev/null')


def _get_dist_path(directory: Path):
    return Path(f'{directory.absolute()}/{DIST}')


def _get_lambda_path_from_root(lambda_dir: str):
    return Path(f'./{lambda_dir}')


def _remove_dist(directory: Path):
    dist_path = _get_dist_path(directory)
    return remove_dir(dist_path)


def _create_dist_and_copy_files(directory: Path) -> Path:
    dist_path = _get_dist_path(directory)
    remove_dir(dist_path)
    copytree(directory, dist_path)
    return dist_path


def _run_zip(directory: Path):
    with ChangeDir(directory):
        zip_name = f'{directory.parent.name}.zip'
        execute_shell_command(f'zip -r {zip_name} . >> /dev/null')


# TODO this part could be more functional
def _create_zip_for_lambda_dir(d):
    if COMMON_DIRECTORY in d.name:
        return List(f'Ignoring {COMMON_DIRECTORY}: {d}')
    else:
        dist_of_dir = _create_dist_and_copy_files(d)
        if _requires_pip_install(dist_of_dir):
            _run_pip_install(dist_of_dir)
        _run_zip(dist_of_dir)
        return List(f'Created zip for {d}')


def _check_root_dir(lambda_dir):
    if not any([d.name == lambda_dir for d in find_all_non_hidden_dirs(Path('.'))]):
        return Left(f'Did not find a "{lambda_dir}" directory in {Path(".").absolute()}. Did you run this command from (a file in) the root of your project?')
    return Right(lambda_dir)


def _check_dir_has_sub_dirs(lambda_dir):
    if len(find_all_non_hidden_dirs(_get_lambda_path_from_root(lambda_dir))) == 0:
        return Left(f'Directory {lambda_dir} does not contain any subdirectories')
    return Right(lambda_dir)


def _check_dirs_contain_python(lambda_dir):
    for d in find_all_non_hidden_dirs(_get_lambda_path_from_root(lambda_dir)):
        # TODO should ignore common
        if not any([x.name.endswith('.py') for x in find_all_non_hidden_files(d)]):
            return Left(f'Could not find python files in {d}')
    return Right(lambda_dir)


def _print_and_exit_with_error_code_if_left(result):
    print(result.value) if type(result) == Left else [print(r) for r in result]
    if type(result) == Left:
        exit(1)


def _check_requirements(lambda_dir):
    return Just(lambda_dir) >> _check_root_dir >> _check_dir_has_sub_dirs >> _check_dirs_contain_python


def _build_stack_commands(stack_data: StackData, prefix):
    # TODO could do check: if path of codeuri refers to something local, use this.
    #   else use python commands: create_change_set -> wait -> execute_change_set
    return List(f'aws cloudformation package --template-file {stack_data.template_name} --s3-bucket "{stack_data.bucket}" --s3-prefix "{prefix}" --output-template-file outputSamTemplate.yaml',
                f'aws cloudformation deploy --template-file outputSamTemplate.yaml --stack-name {stack_data.stack_name} --capabilities CAPABILITY_IAM',
                'rm outputSamTemplate.yaml')  # use path for this?


def remove_dists(lambda_dir: str = 'lambdas'):
    result = _check_requirements(lambda_dir) >> get_as_path >> find_all_non_hidden_dirs >> _remove_dist
    _print_and_exit_with_error_code_if_left(result)


def create_zips(lambda_dir: str = 'lambdas'):
    result = _check_requirements(lambda_dir) >> get_as_path >> find_all_non_hidden_dirs >> _create_zip_for_lambda_dir
    _print_and_exit_with_error_code_if_left(result)


def create_stack(stack_data: StackData) -> None:
    prefix = stack_data.bucket_prefix if stack_data.bucket_prefix else stack_data.stack_name
    result = _build_stack_commands(stack_data, prefix) >> execute_shell_command
    _print_and_exit_with_error_code_if_left(result)


def deploy(stack_data: StackData, lambda_dir: str = 'lambdas') -> None:
    create_zips(lambda_dir)
    create_stack(stack_data)
    remove_dists(lambda_dir)
