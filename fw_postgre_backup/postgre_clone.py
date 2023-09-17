import datetime

from fw_automations_utils.logger_functionality import get_config_and_set_logger
from fw_postgre_backup.postgre_commands import PostgresqlCommand
from fw_server_communications.inventory_communications import report_to_server
from fw_server_communications.mail_reports import send_mail_mime

if __name__ == "__main__":
    backup_config = {
        'clone_backup_db': {
            'medoc03': 'postgre0101.bs.local.erc',
            'medoc01': 'postgre0101.bs.local.erc',
        },
        "special_url": "https://inventory0201.bs.local.erc/special",
        "token_url": "https://inventory0201.bs.local.erc/token",
        "public_key": "public.pem",
        'send_report_mail': True,
        'send_success_mail': True,
        'send_report_web': True,
        'send_report_code': 35,
        "from_mail": "Department_BSP@erc.ua",
        "to_mail": "Department_BSP@erc.ua",
        "proxy": "http://fw01.bs.local.erc:8080/",
        'log_file': '/home/admin_root/clone.log',
        "server": "WEBLOCAL0201.local.erc",
        "port": 25,
        "safe_time": 4,
        'log_level': 'DEBUG',
    }
    backup_config, log_file = get_config_and_set_logger('clone.json', exit_on_error=False,
                                                        default_config=backup_config)
    backup = PostgresqlCommand()
    db_cloned = 0
    messages = []
    clone_list = backup_config.get('clone_backup_db', {})
    for db, source in clone_list.items():
        start_time = datetime.datetime.now()
        if backup.clone_db(db, source):
            db_cloned += 1
            delta = str(datetime.datetime.now() - start_time).split('.', 2)[0]
            messages.append(f'DB {db}:{source} -cloned, operation time: {delta}')
        else:
            delta = str(datetime.datetime.now() - start_time).split('.', 2)[0]
            messages.append(f'CLONE ERROR ON DB {db} from {source} operation time: {delta}')
    message = '\n'.join(messages)
    if db_cloned == 0:
        report_to_server(message, backup_config, True)
        send_mail_mime(message, backup_config, is_error=True, files=[log_file])
    elif len(clone_list) > db_cloned:
        report_to_server('\n'.join(messages), backup_config, True)
        send_mail_mime(message, backup_config, is_error=True, files=[log_file])
    else:
        report_to_server('\n'.join(messages), backup_config, False)
        if backup_config.get('send_success_mail', False):
            send_mail_mime(message, backup_config, is_error=False)
