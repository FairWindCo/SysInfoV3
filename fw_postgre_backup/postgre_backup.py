import logging

from fw_postgre_backup.postgre_commands import process_backup
from fw_utils.mounting import mount_protocol
from fw_utils.utils import execute_os_command

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    backup_config = {
        'kerberos_key_file': '/etc/krb5.keytab',
        'backup_db': ['medoc03'],
        'mount_points': {
            '//bkp0201.bs.local.erc/postgresql': '/mnt/bkp0201',
            '//bkp0101.bs.local.erc/postgresql': '/mnt/bkp0101',
        },
        # 'destination_dirs': ['/mnt/bkp0201', '/mnt/bkp0101']
        'tmp_dir': '/tmp',
        'use_temp': False
    }
    logging.debug(f"CURRENT CONFIG: {backup_config}")
    execute_os_command('echo "test"', in_sudo=True, has_pipe=True, as_user='postgres')
    mount_protocol(backup_config, process_backup)
