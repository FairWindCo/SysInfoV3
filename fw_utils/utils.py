import logging
import os
import shutil
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError


def append_data_to_config(config_dict: dict, key: str = 'error_list', value: str = None):
    list_values = config_dict.get(key, [])
    list_values.append(value)
    config_dict[key] = list_values


def create_path(path_for_create: str):
    path_element = ''
    while True:
        current_path_element, path_for_create = os.path.split(path_for_create)
        if not current_path_element:
            path_element = os.path.join(path_element, path_for_create)
        else:
            path_element = os.path.join(path_element, current_path_element)
        if not os.path.exists(path_element):
            try:
                os.mkdir(path_element)
            except Exception as io:
                logging.error(f"ERROR path create {path_element}: {io}")
                return False
        if not current_path_element:
            break
    return True


def change_permissions(path: str, user: str = 'postgres', rights: int = 777):
    if os.path.exists(path):
        logging.debug(f"change attribute on folder: {path}")
        os.chmod(path, rights)
        shutil.chown(path, user=user)
        return True
    else:
        logging.warning(f"Path {path} - does not exists!")
        return False


def check_folder(path: str, user: str = 'postgres', rights: int = 770, can_create: bool = True):
    if os.path.exists(path):
        return change_permissions(path, user, rights)
    elif can_create:
        create_path(path)
        return change_permissions(path, user, rights)
    else:
        logging.warning(f"Path {path} - does not exists!")
        return False


def execute_os_command(*commands: str, in_sudo: bool = True, has_pipe: bool = False,
                       as_user: str = None, timeout: int = None, in_shell: bool = False,
                       working_dir: str = None, like_login_sudo: bool = True):
    command_for_execute = []
    if in_sudo:
        command_for_execute.append('sudo')
        if as_user:
            command_for_execute.append('-u')
            command_for_execute.append(as_user)
        if working_dir:
            command_for_execute.append('-D')
            command_for_execute.append(working_dir)
        if like_login_sudo:
            command_for_execute.append('-i')
    if has_pipe:
        command_for_execute.append('--')
        command_for_execute.append('sh')
        command_for_execute.append('-c')
        #command_for_execute.append(f"\'{' '.join(commands)}\'")
        command_for_execute.append(' '.join(commands))
    else:
        command_for_execute.extend(commands)
    # logging.debug(f'ARGS: {command_for_execute} ')
    try:
        logging.debug(f'COMMAND {" ".join(command_for_execute)} ')
    except TypeError:
        logging.warning(f'COMMAND ARGUMENTS INCORRECT: {command_for_execute} ')
    try:
        subp = Popen(command_for_execute, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=in_shell)
        output_stream, err_stream = subp.communicate(timeout=timeout)
        if subp.returncode != 0:
            logging.warning(f"RETURN CODE NON ZERO: {subp.returncode} {err_stream.decode()}")
        return subp.returncode == 0, subp.returncode, output_stream, err_stream
    except TimeoutExpired:
        logging.warning("Timeout")
    except SubprocessError as e:
        logging.error(f"Sub process error: {e}")
    except OSError as o:
        logging.error(f"OS error: {o}")
    return False, -1, None, None
