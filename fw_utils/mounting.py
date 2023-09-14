import logging
import os.path

from fw_utils.utils import create_path, execute_os_command
from kerberos.linux_kerberos import init_key


class MountControl:
    def __init__(self, device_for_mount: str, mount_point: str, kerberos_keytab: str = None) -> None:
        super().__init__()
        self.mount_device = device_for_mount
        self.mount_point = mount_point
        self.kerberos_keytab = kerberos_keytab

    def check_mount_point_exists(self, try_create: bool = True):
        if os.path.exists(self.mount_point):
            return True
        else:
            return create_path(self.mount_point)

    def mount(self):
        if self.check_mount_point_exists():
            if self.kerberos_keytab:
                if not init_key(self.kerberos_keytab, in_sudo=True):
                    logging.warning(f"init key error")
            execute_os_command('mount', '-t', 'cifs', '-o', 'sec=krb5',
                               self.mount_device, self.mount_point,
                               in_sudo=True)
        else:
            logging.error(f"NO MOUNT POINT:{self.mount_point}")

    def unmount(self):
        execute_os_command('umount', self.mount_point, in_sudo=True)
