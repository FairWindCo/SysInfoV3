import datetime
import logging
import os.path
import shutil

from fw_utils.clear_old_file import clear_old_backup
from fw_utils.utils import execute_os_command, check_folder, sizeof_fmt


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

    def create_backup_file(self, db_name: str, backup_name: str) -> bool:
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

    def create_db(self, db_name: str, collacation: str = 'uk_UA.UTF-8',
                  owner=None, time_zone="Europe/Kiev"):
        db_owner = db_name if owner is None else owner
        command = ['/usr/bin/psql',
                   f'--command="CREATE DATABASE \\"{db_name}\\" WITH OWNER = {db_owner} LOCALE = \\"{collacation}\\" TEMPLATE=template0"']
        result, _, _, err = execute_os_command(*command, in_sudo=True, has_pipe=True,
                                               as_user=self.command_user, in_shell=False, working_dir=None)
        if not result:
            logging.error(f"CREATE DB ERROR: {err}")
            return result
        if time_zone:
            return self.config_timezone(db_name, time_zone)
        return result

    def config_timezone(self, db_name: str, time_zone="Europe/Kiev"):
        command = ['/usr/bin/psql', f'--dbname={db_name}',
                   f'--command="SET TIME ZONE \\"{time_zone}\\""']
        result, _, _, err = execute_os_command(*command, in_sudo=True, has_pipe=True,
                                               as_user=self.command_user, in_shell=False, working_dir=None)
        if not result:
            logging.error(f"CONFIG DB ERROR: {err}")
        return result

    def drop_db(self, db_name: str):
        command = ['/usr/bin/psql',
                   f'--command="DROP DATABASE \\"{db_name}\\" WITH (FORCE)"']
        result, _, _, err = execute_os_command(*command, in_sudo=True, has_pipe=True,
                                               as_user=self.command_user, in_shell=False, working_dir=None)
        if not result:
            if err.find(b'does not exist\n') > 0:
                logging.warning(f"DATABASE: {db_name} - does not exist!")
                return True
            logging.error(f"DROP DB ERROR: {err}")
        return result

    def re_create_db(self, db_name: str, collacation: str = 'uk_UA.UTF-8',
                     owner=None, time_zone="Europe/Kiev"):
        if self.drop_db(db_name):
            return self.create_db(db_name, collacation, owner, time_zone)
        return False

    def clone_db(self, db_name: str, source_host: str, dest_db_name: str = None, re_create_db=True) -> bool:
        dest_db_name = dest_db_name if dest_db_name else db_name
        host_src = f'--host={source_host}' if source_host else ''
        host_dsr = f'--host={self.connection_host}' if self.connection_host else ''

        if re_create_db:
            self.re_create_db(dest_db_name)
            command = f'/usr/bin/pg_dump --dbname={db_name} {host_src} -F c | /usr/bin/pg_restore {host_dsr} -d {dest_db_name}'
        else:
            command = f'/usr/bin/pg_dump --dbname={db_name} {host_src} -F c | /usr/bin/pg_restore {host_dsr} -d {dest_db_name} -c'

        result, _, _, err = execute_os_command(command, in_sudo=True, has_pipe=True,
                                               as_user=self.command_user, in_shell=False, working_dir=None)
        if not result:
            logging.error(f"BACKUP ERROR: {err}")
        return result

    def get_backup_file_name(self, db_name) -> str:
        current_date = datetime.datetime.now().strftime(self.date_template)
        return self.backup_file_format.format(db_name, current_date)

    def create_date_backup(self, db_name) -> bool:
        return self.create_backup_file(db_name, self.get_backup_file_name(db_name))

    def get_backup_full_path(self, db_name) -> str:
        return os.path.join(self.dir_for_backup, self.get_backup_file_name(db_name))

    def copy_backup_to_dest(self, db_name, dest_folder) -> bool:
        if check_folder(dest_folder, user=self.command_user, can_create=self.can_create_backup_folder,
                        rights=self.backup_folder_permissions):
            src = self.get_backup_full_path(db_name)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dest_folder)
                    return True
                except OSError as e:
                    logging.error(f"FILE COPY {src} TO {dest_folder} - {e}")
                    return False
            else:
                logging.error(f"FILE BACKUP {src} - not exists!")
                return False
        else:
            logging.error(f"NO DEST PATH {dest_folder}")
            return False

    def clear_old_backup(self, db_name: str, dir_with_backups: str = None) -> bool:
        if dir_with_backups is None:
            dir_with_backups = self.dir_for_backup
        format_search = self.clear_backup_file_format % db_name
        return clear_old_backup(dir_with_backups, format_search,
                                self.delete_file_age_days,
                                self.safe_last_files_num)

    def delete_backup(self, db_name: str) -> bool:
        full_path = self.get_backup_full_path(db_name)
        try:
            os.remove(full_path)
            return True
        except OSError as e:
            logging.error(f"DELETE FILE ERROR: {full_path} - {e}")
            return False

    def backup_info(self, db_name: str):
        full_path = self.get_backup_full_path(db_name)
        if os.path.exists(full_path):
            stat = os.stat(full_path)
            return stat.st_size, stat.st_mtime
        else:
            return 0, None


def process_backup(config: dict, stage):
    result = True
    use_tmp = config.get('use_temp', True)
    destination_dirs = config.get('destination_dirs', []).copy()
    if use_tmp:
        directory_to_backup = config.get('tmp_dir', None)
    else:
        if destination_dirs:
            directory_to_backup = destination_dirs.pop()
        else:
            stage.set_error()
            stage.add_message("NO DESTINATION FOLDERS")
            return False
    backup = PostgresqlCommand(backup_dir=directory_to_backup)
    for db in config.get('backup_db', []):
        res = backup.create_date_backup(db)
        result &= res
        if res:
            size, _ = backup.backup_info(db)
            stage.add_message(f'DB {db} backup size: {sizeof_fmt(size)}')
        for dest_dir in destination_dirs:
            if res:
                result &= backup.copy_backup_to_dest(db, dest_dir)
                result &= backup.clear_old_backup(db, dest_dir)
        if use_tmp and res:
            result &= backup.delete_backup(db)
        else:
            result &= backup.clear_old_backup(db)
    if not result:
        stage.set_warning()
    return result
