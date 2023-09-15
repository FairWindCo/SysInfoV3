import datetime
import logging
import os.path
import shutil

from fw_utils.clear_old_file import clear_old_backup
from fw_utils.utils import execute_os_command, check_folder


class PostgresqlCommand:
    date_template = "%d%m%y"
    backup_file_format = '{}_{}.dmp.gz'
    clear_backup_file_format = '%s_[0-9]{6}\.dmp\.gz'
    delete_file_age_days = 7
    safe_last_files_num = 5
    can_create_backup_folder = True
    backup_folder_permissions = 0o777

    def __init__(self, system_user: str = 'postgres', host: str = None, backup_dir: str = '/tmp') -> None:
        super().__init__()
        self.command_user = system_user
        self.connection_host = host
        self.dir_for_backup = backup_dir

    def create_backup_file(self, db_name: str, backup_name: str):
        backup_path = os.path.join(self.dir_for_backup, backup_name)
        if check_folder(self.dir_for_backup, user=self.command_user, can_create=self.can_create_backup_folder,
                        rights=self.backup_folder_permissions):
            if self.connection_host:
                command = f'cd /tmp; /usr/bin/pg_dump --dbname={db_name} --host={self.connection_host} -F c | /usr/bin/gzip -9 -c >{backup_path}'
            else:
                command = f'cd /tmp; /usr/bin/pg_dump --dbname={db_name} -F c | /usr/bin/gzip -9 -c >{backup_path}'
            # result, _, _, err = execute_os_command(command, in_sudo=True, has_pipe=True, as_user=self.command_user)
            result, _, _, err = execute_os_command(command, in_sudo=True, has_pipe=True,
                                                   as_user=self.command_user, in_shell=False, working_dir=None)
            if not result:
                logging.error(f"BACKUP ERROR: {err}")
            return result
        else:
            return False
        # self.execute_command_with_pipe(command)

    def get_backup_file_name(self, db_name):
        current_date = datetime.datetime.now().strftime(self.date_template)
        return self.backup_file_format.format(db_name, current_date)

    def create_date_backup(self, db_name):
        self.create_backup_file(db_name, self.get_backup_file_name(db_name))

    def get_backup_full_path(self, db_name):
        return os.path.join(self.dir_for_backup, self.get_backup_file_name(db_name))

    def copy_backup_to_dest(self, db_name, dest_folder):
        if check_folder(dest_folder, user=self.command_user, can_create=self.can_create_backup_folder,
                        rights=self.backup_folder_permissions):
            src = self.get_backup_full_path(db_name)
            if os.path.exists(src):
                shutil.copy2(src, dest_folder)
            else:
                logging.error(f"FILE BACKUP {src} - not exists!")
        else:
            logging.error(f"NO DEST PATH {dest_folder}")

    def clear_old_backup(self, db_name: str, dir_with_backups: str = None):
        if dir_with_backups is None:
            dir_with_backups = self.dir_for_backup
        format_search = self.clear_backup_file_format % db_name
        clear_old_backup(dir_with_backups, format_search,
                         self.delete_file_age_days,
                         self.safe_last_files_num)

    def delete_backup(self, db_name: str):
        full_path = self.get_backup_full_path(db_name)
        try:
            os.remove(full_path)
        except OSError as e:
            logging.error(f"DELETE FILE ERROR: {full_path} - {e}")

    def backup_info(self, db_name: str):
        full_path = self.get_backup_full_path(db_name)
        if os.path.exists(full_path):
            stat = os.stat(full_path)
            return stat.st_size, stat.st_mtime
        else:
            return 0, None


def process_backup(config: dict):
    use_tmp = config.get('use_temp', True)
    destination_dirs = config.get('destination_dirs', []).copy()
    if use_tmp:
        directory_to_backup = config.get('tmp_dir', None)
    else:
        directory_to_backup = destination_dirs.pop()
    backup = PostgresqlCommand(backup_dir=directory_to_backup)
    for db in config.get('backup_db', []):
        backup.create_date_backup(db)
        for dest_dir in destination_dirs:
            backup.copy_backup_to_dest(db, dest_dir)
            backup.clear_old_backup(db, dest_dir)
        if use_tmp:
            backup.delete_backup(db)
