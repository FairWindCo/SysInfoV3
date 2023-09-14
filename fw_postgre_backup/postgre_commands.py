import datetime
import os.path
from subprocess import Popen, PIPE

from fw_utils.clear_old_file import clear_old_backup


class PostgresqlCommand:
    date_template = "%d%m%y"
    backup_file_format = '{}_{}.dmp.gz'
    clear_backup_file_format = '%s_[0-9]{6}\.dmp\.gz'
    delete_file_age_days = 7
    safe_last_files_num = 5

    def __init__(self, system_user: str = 'postgres', host: str = None, backup_dir: str = '/mnt') -> None:
        super().__init__()
        self.command_user = system_user
        self.connection_host = host
        self.dir_for_backup = backup_dir

    def execute_command_with_pipe(self, command):
        commands_args = ['sudo', '-u', self.command_user, 'bash', '-c', command]
        subp = Popen(commands_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        subp.wait()

    def create_backup_file(self, db_name: str, backup_name: str):
        backup_path = os.path.join(self.dir_for_backup, backup_name)
        if self.connection_host:
            command = f'pg_dump --dbname={db_name} --host={self.connection_host} -F d | gzip -9 -c >{backup_path}'
        else:
            command = f'pg_dump --dbname={db_name} -F d | gzip -9 -c >{backup_path}'
        self.execute_command_with_pipe(command)

    def create_date_backup(self, db_name):
        current_date = datetime.datetime.now().strftime(self.date_template)
        file_name = self.backup_file_format.format(db_name, current_date)
        self.create_backup_file(db_name, file_name)

    def clear_old_backup(self, db_name):
        format_search = self.clear_backup_file_format % db_name
        clear_old_backup(self.dir_for_backup, format_search,
                         self.delete_file_age_days,
                         self.safe_last_files_num)
