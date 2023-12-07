import logging

from fw_utils.utils import execute_os_command, check_folder
from kerberos.linux_kerberos import init_key


class MountControl:
    mount_point_permission = 0o777
    mount_point_owner = 'postgres'
    mount_options = 'sec=krb5,dir_mode=0777,file_mode=0666'

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
            commands = ['mount', '-t', 'cifs']
            if self.mount_options:
                commands.append('-o')
                commands.append(self.mount_options)
            result, *_ = execute_os_command(*commands,
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
        result, *_ = execute_os_command('umount', self.mount_point, in_sudo=True)
        return result


def mount_protocol(config: dict, execute_procedure, stage, stop_if_error: bool = False):
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
                    if stop_if_error:
                        stage.add_message(f"MOUNT ERROR: {device} {mount_point}")
                        stage.set_error()
                        return
                    else:
                        stage.set_warning()
            else:
                destination_dirs.append(mounter.mount_point)
    if not destination_dirs:
        logging.error("MOUNT ERROR")
        stage.add_message("NO FOLDERS MOUNT")
        stage.set_error()
        return
    config['destination_dirs'] = destination_dirs
    execute_procedure(config, stage)
    for mounter in mounter_controls:
        result = mounter.unmount()
        if not result:
            stage.set_warning()
