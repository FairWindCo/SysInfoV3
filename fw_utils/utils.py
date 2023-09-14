import logging
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError


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


def execute_os_command(command: str, *arguments: str, in_sudo: bool = True, has_pipe: bool = False,
                       as_user: str = None, timeout: int = None):
    command_for_execute = []
    if in_sudo:
        command_for_execute.append('sudo')
        if as_user:
            command_for_execute.append('-u')
            command_for_execute.append(as_user)
    if has_pipe:
        command_for_execute.append('bash')
        command_for_execute.append('-c')
        command_for_execute.append(' '.join([command, *arguments]))
    else:
        command_for_execute.append(command)
        command_for_execute.extend(arguments)
    logging.debug(f'COMMAND {" ".join(command_for_execute)} ')
    try:
        subp = Popen(command_for_execute, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output_stream, err_stream = subp.communicate(timeout=timeout)
        if subp.returncode == 0:
            logging.warning(f"RETURN CODE NON ZERO: {subp.returncode} {subp.stderr.readlines()}")
        return subp.returncode == 0, subp.returncode, output_stream, err_stream
    except TimeoutExpired:
        logging.warning("Timeout")
    except SubprocessError as e:
        logging.error(f"Sub process error: {e}")
    except OSError as o:
        logging.error(f"OS error: {o}")
    return False, -1, None, None
