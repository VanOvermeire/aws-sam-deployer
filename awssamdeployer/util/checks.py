from functools import partial
from pathlib import Path

from pymonad import Left, Right, Just

from awssamdeployer.util.constants import COMMON_DIRECTORY
from awssamdeployer.util.util import find_all_non_hidden_dirs, find_all_non_hidden_files, _get_lambda_path_from_root, StackData, get_as_path


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
        # checks for common could be better
        if not any([x.name.endswith('.py') or COMMON_DIRECTORY in d.name for x in find_all_non_hidden_files(d)]):
            return Left(f'Could not find python files in {d}')
    return Right(lambda_dir)


def _check_template_exists(stack_data: StackData, directory: Path):
    return Right('Template exists') if any([d.name == stack_data.template_name for d in find_all_non_hidden_files(directory)]) else Left(f'Template {stack_data.template_name} does not exist')


def check_requirements(lambda_dir):
    return Just(lambda_dir) >> _check_root_dir >> _check_dir_has_sub_dirs >> _check_dirs_contain_python


def check_stack_requirements(stack_data: StackData):
    # also: check whether bucket exists? does require boto3 dependency
    return get_as_path('.') >> partial(_check_template_exists, stack_data) >> Just(stack_data)
