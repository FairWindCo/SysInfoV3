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
            result, *_ = execute_os_command('mount', '-t', 'cifs', '-o', 'sec=krb5',
                                            self.mount_device, self.mount_point,
                                            in_sudo=True)
            return result
        else:
            logging.error(f"NO MOUNT POINT:{self.mount_point}")
            return False

    def check_mount(self):
        result, _, mounts, _ = execute_os_command('mount')
        if result:
            for mount_line in mounts.split(b'\n'):
                if mount_line:
                    mount_elements = mount_line.split(b' ')[:3]
                    print(mount_elements)
                    device, _, mount_point = mount_elements
                    if device.decode() == self.mount_device and mount_point.decode() == self.mount_point:
                        return True
            return False
        else:
            logging.error("ERROR EXECUTE MOUNT")
            return False

    def unmount(self):
        execute_os_command('umount', self.mount_point, in_sudo=True)
