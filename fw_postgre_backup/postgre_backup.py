import logging

from fw_utils.mounting import mount_protocol

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    backup_config = {
        'kerberos_key_file': '/etc/posgre0102.keytab',
        'backup_db': ['medoc03'],
        'mount_points': {
            '//bkp0201.bs.local.erc/postgresql': '/mnt/bkp0201',
            '//bkp0101.bs.local.erc/postgresql': '/mnt/bkp0101',
        },
        # 'destination_dirs': ['/mnt/bkp0201', '/mnt/bkp0101']
    }
    logging.debug(f"CURRENT CONFIG: {backup_config}")
    mount_protocol(backup_config, lambda c: print(c))
