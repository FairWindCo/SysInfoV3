import datetime

from fw_automations_utils.logger_functionality import get_config_and_set_logger
from fw_postgre_backup.postgre_commands import PostgresqlCommand
from fw_server_communications.inventory_communications import report_to_server
from fw_server_communications.mail_reports import send_mail_mime

if __name__ == "__main__":
    backup_config = {
        'clone_backup_db': ['medoc03'],
        "special_url": "https://inventory0201.bs.local.erc/special",
        "public_key": "public.pem",
        'send_report_mail': True,
        'send_success_mail': True,
        'send_report_web': True,
        'send_report_code': 35,
        "from_mail": "bspd@local.erc",
        "to_mail": "bspd@local.erc",
        "server": "web02.local.erc",
        "port": 25,
        "safe_time": 4,
    }
    backup_config, log_file = get_config_and_set_logger('clone.json', exit_on_error=False,
                                                        default_config=backup_config)
    backup = PostgresqlCommand()
    db_cloned = 0
    messages = []
    clone_list = backup_config.get('clone_backup_db', [])
    for db in clone_list:
        start_time = datetime.datetime.now()
        if backup.clone_db(db):
            db_cloned += 1
            delta = str(start_time - datetime.datetime.now()).split('.', 2)[0]
            messages.append(f'DB {db} -cloned, operation time: {delta}')
        else:
            delta = str(start_time - datetime.datetime.now()).split('.', 2)[0]
            messages.append(f'CLONE ERROR ON DB {db} operation time: {delta}')
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
