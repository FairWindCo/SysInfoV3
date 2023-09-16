from fw_automations_utils.logger_functionality import get_config_and_set_logger
from fw_postgre_backup.postgre_commands import process_backup
from fw_server_communications.inventory_communications import report_to_server
from fw_server_communications.mail_reports import send_mail_mime
from fw_utils.mounting import mount_protocol
from fw_utils.stager import Stage

if __name__ == "__main__":
    # logging.getLogger().setLevel(logging.DEBUG)
    # logging.basicConfig(filename='/home/admin_root/example.log', encoding='utf-8', level=logging.DEBUG)
    backup_config = {
        'kerberos_key_file': '/etc/krb5.keytab',
        'backup_db': ['medoc03'],
        'mount_points': {
            '//bkp0201.bs.local.erc/postgresql': '/mnt/bkp0201',
            '//bkp0101.bs.local.erc/postgresql': '/mnt/bkp0101',
        },
        # 'destination_dirs': ['/mnt/bkp0201', '/mnt/bkp0101']
        'tmp_dir': '/tmp',
        'use_temp': False,
        "special_url": "https://inventory0201.bs.local.erc/special",
        "token_url": "https://inventory0201.bs.local.erc/token",
        "public_key": "public.pem",
        'send_report_mail': True,
        'send_success_mail': True,
        'send_report_web': True,
        'send_report_code': 37,
        "from_mail": "bspd@local.erc",
        "to_mail": "bspd@local.erc",
        "server": "web02.local.erc",
        "port": 25,
        "safe_time": 4,
    }
    backup_config, log_file = get_config_and_set_logger('backup.json', exit_on_error=False,
                                                        default_config=backup_config)
    # execute_os_command('echo "test"', in_sudo=True, has_pipe=True, as_user='postgres')
    stage = Stage()
    mount_protocol(backup_config, process_backup, stage)
    stage.end_work(True)
    if not stage.finish_success:
        msg = f"BACKUP POSTGRESQL ERROR! time: {stage.work_time}"
        report_to_server(msg, backup_config, True)
        send_mail_mime(msg, backup_config, is_error=True, files=[log_file])
    else:
        if stage.warning:
            msg = f"BACKUP POSTGRESQL WITH WARNINGS! time: {stage.work_time}"
        else:
            msg = f"BACKUP POSTGRESQL SUCCESS! time: {stage.work_time}"
        report_to_server(msg, backup_config, False)
        if backup_config.get('send_success_mail', False) or stage.warning:
            send_mail_mime(msg, backup_config, is_error=False, files=[log_file])
