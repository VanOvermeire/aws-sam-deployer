from pathlib import Path
from shutil import copytree

from awssamdeployer.util.constants import COMMON_DIRECTORY, DIST
from awssamdeployer.util.util import StackData, ChangeDir, execute_shell_commands, find_all_non_hidden_files, find_all_non_hidden_dirs, remove_dir


def _requires_pip_install(directory: Path):
    return 'requirements.txt' in [x.name for x in find_all_non_hidden_files(directory.absolute())]


def _run_pip_install(directory: Path):
    with ChangeDir(directory):
        print(f'Running pip install in directory {directory}')
        execute_shell_commands(['pip3 install -r requirements.txt -t . >> /dev/null'])


def _get_dist_path(directory: Path):
    return Path(f'{directory.absolute()}/{DIST}')


def _get_lambda_path_from_root(lambda_dir: str):
    return Path(f'./{lambda_dir}')


def _remove_dist(directory: Path):
    dist_path = _get_dist_path(directory)
    print(f'Removing {dist_path}')
    remove_dir(dist_path)


def create_dist_and_copy_files(directory: Path) -> Path:
    dist_path = _get_dist_path(directory)
    remove_dir(dist_path)
    copytree(directory, dist_path)

    return dist_path


def _run_zip(directory: Path):
    with ChangeDir(directory):
        print(f'Creating zip in directory {directory}')
        zip_name = f'{directory.parent.name}.zip'
        execute_shell_commands([
            f'zip -r {zip_name} . >> /dev/null',
        ])


def _check_if_requirements_ok(lambda_dir: str):
    dirs = find_all_non_hidden_dirs(Path('.'))
    dir_names = [d.name for d in dirs]

    if lambda_dir not in dir_names:
        this_dir = Path('.').absolute()
        print(f'Did not find a "{lambda_dir}" directory in {this_dir}. Did you run this command from (a file in) the root of your project?')
        return False
    dirs = find_all_non_hidden_dirs(_get_lambda_path_from_root(lambda_dir))

    if len(dirs) == 0:
        print(f'Directory {lambda_dir} seems to be empty')
        return False

    for d in dirs:
        # TODO should ignore common
        file_names = [x.name for x in find_all_non_hidden_files(d)]
        any_python_files = any([x.endswith('.py') for x in file_names])

        if not any_python_files:
            print(f'Could not find python files in {d}')
            return False
    return True


def remove_dists(lambda_dir: str = 'lambdas') -> None:
    if _check_if_requirements_ok(lambda_dir):
        for d in find_all_non_hidden_dirs(_get_lambda_path_from_root(lambda_dir)):
            _remove_dist(d)
    else:
        exit(1)


def create_zips(lambda_dir: str = 'lambdas'):
    if _check_if_requirements_ok(lambda_dir):
        for d in find_all_non_hidden_dirs(_get_lambda_path_from_root(lambda_dir)):
            if COMMON_DIRECTORY in d.name:
                print(f'Ignoring {COMMON_DIRECTORY}: {d}')
            else:
                dist_of_dir = create_dist_and_copy_files(d)
                if _requires_pip_install(dist_of_dir):
                    _run_pip_install(dist_of_dir)
                _run_zip(dist_of_dir)
    else:
        exit(1)


def create_stack(stack_data: StackData) -> None:
    prefix = stack_data.bucket_prefix if stack_data.bucket_prefix else stack_data.stack_name
    execute_shell_commands([
        # TODO could do check: if path of codeuri refers to something local, use this. else use python commands: create_change_set -> wait -> execute_change_set
        f'aws cloudformation package --template-file {stack_data.template_name} --s3-bucket "{stack_data.bucket}" --s3-prefix "{prefix}" --output-template-file outputSamTemplate.yaml',
        f'aws cloudformation deploy --template-file outputSamTemplate.yaml --stack-name {stack_data.stack_name} --capabilities CAPABILITY_IAM',
        'rm outputSamTemplate.yaml',  # TODO use path for this?
    ])


def deploy(stack_data: StackData, lambda_dir: str = 'lambdas') -> None:
    if _check_if_requirements_ok:
        create_zips(lambda_dir)
        create_stack(stack_data)
        remove_dists(lambda_dir)
    else:
        exit(1)
