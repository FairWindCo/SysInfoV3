import logging
import os.path
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError


def create_path(path_for_create: str):
    path_element = ''
    while True:
        current_path_element, path_for_create = os.path.split(path_for_create)
        path_element = os.path.join(path_element, current_path_element)
        if not os.path.exists(path_element):
            try:
                os.mkdir(path_element)
            except Exception as io:
                logging.error(f"ERROR path create {path_element}: {io}")
                return False
        if not path_for_create:
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
        subp.communicate(timeout=timeout)
        return subp.returncode == 0, subp.returncode, subp.stdout, subp.stderr
    except TimeoutExpired:
        logging.warning("Timeout")
    except SubprocessError as e:
        logging.error(f"Sub process error: {e}")
    except OSError as o:
        logging.error(f"OS error: {o}")
    return False, -1, None, None


class moun:
    def __init__(self, device_for_mount: str, mount_point: str) -> None:
        super().__init__()
        self.mount_device = device_for_mount
        self.mount_point = mount_point

    def check_mount_point_exists(self, try_create: bool = True):
        if os.path.exists(self.mount_point):
            return True
        else:
            return create_path(self.mount_point)

    def mount(self):
        execute_os_command('mount', '-t', 'cifs', '-o', 'sec=krb5', self.mount_device, self.mount_point, in_sudo=True)

    def unmount(self):
        execute_os_command('umount', self.mount_point, in_sudo=True)
