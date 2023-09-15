import logging

from fw_postgre_backup.postgre_commands import PostgresqlCommand

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    backup_config = {
        'clone_backup_db': ['medoc03'],
    }
    logging.debug(f"CURRENT CONFIG: {backup_config}")
    backup = PostgresqlCommand()
    for db in backup_config.get('clone_backup_db', []):
        backup.clone_db(db)
