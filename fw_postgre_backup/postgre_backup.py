import logging

from fw_utils.mounting import MountControl

if __name__ == "__main__":
    backup_config = {
        'kerberos_key_file': '/etc/posgre0102.keytab',
        'backup_db': ['medoc03'],
        'mount_points': {
            '//bkp0201.bs.local.erc/postgresql': '/mnt/bkp0201',
            '//bkp0101.bs.local.erc/postgresql': '/mnt/bkp0101',
        },
        # 'destination_dirs': ['/mnt/bkp0201', '/mnt/bkp0101']
    }
    logging.getLogger().setLevel(logging.DEBUG)
    destination_dirs = backup_config.get('destination_dirs', [])
    mounter_controls = []
    if 'mount_points' in backup_config:
        for device, mount_point in backup_config['mount_points'].items():
            mounter = MountControl(device, mount_point, backup_config.get('kerberos_key_file', None))
            if not mounter.check_mount():
                if mounter.mount():
                    if mounter.check_mount():
                        destination_dirs.append(mounter.mount_point)
                        mounter_controls.append(mounter)
                else:
                    logging.error("MOUNT ERROR")
            else:
                destination_dirs.append(mounter.mount_point)

    # for mounter in mounter_controls:
    #     mounter.unmount()
