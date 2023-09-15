import logging

from fw_utils.utils import execute_os_command, append_data_to_config, check_folder
from kerberos.linux_kerberos import init_key


class MountControl:
    mount_point_permission = 777
    mount_point_owner = 'postgres'

    def __init__(self, device_for_mount: str, mount_point: str, kerberos_keytab: str = None) -> None:
        super().__init__()
        self.mount_device = device_for_mount
        self.mount_point = mount_point
        self.kerberos_keytab = kerberos_keytab

    def check_mount_point_exists(self, try_create: bool = True):
        return check_folder(self.mount_point, self.mount_point_owner, self.mount_point_permission, try_create)

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
                    device, _, mount_point = mount_elements
                    if device.decode() == self.mount_device and mount_point.decode() == self.mount_point:
                        return True
            return False
        else:
            logging.error("ERROR EXECUTE MOUNT")
            return False

    def unmount(self):
        execute_os_command('umount', self.mount_point, in_sudo=True)


def mount_protocol(config: dict, execute_procedure, stop_if_error: bool = False):
    destination_dirs = config.get('destination_dirs', [])
    mounter_controls = []
    if 'mount_points' in config:
        for device, mount_point in config['mount_points'].items():
            mounter = MountControl(device, mount_point, config.get('kerberos_key_file', None))
            if not mounter.check_mount():
                if mounter.mount():
                    if mounter.check_mount():
                        destination_dirs.append(mounter.mount_point)
                        mounter_controls.append(mounter)
                else:
                    logging.error("MOUNT ERROR")
                    append_data_to_config(config, 'errors_list',
                                          f'MOUNT {mounter.mount_device} on {mounter.mount_point}')
                    if stop_if_error:
                        return
            else:
                destination_dirs.append(mounter.mount_point)
    config['destination_dirs'] = destination_dirs
    execute_procedure(config)
    for mounter in mounter_controls:
        mounter.unmount()
