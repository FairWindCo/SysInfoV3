import argparse
import ctypes
import functools
import os
import shutil
from pathlib import Path, PurePath
from typing import Callable

import win32api

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading
from fw_automations_utils.logger_functionality import error, exception, info, setup_logger, warning, IS_ERROR_LOGGED
from fw_server_communications.inventory_communications import report_to_server
from fw_automations_utils.config import get_config
from fw_server_communications.mail_reports import send_mail_ex
from fw_automations_utils.winsys_utils import get_fixed_drives, reboot, system_dick_cleanup, disk_space, kill_control, check_work_in_temp


class AdminStateUnknownError(Exception):
    """Cannot determine whether the user is an admin."""
    pass


def on_error(function, path, excinfo):
    error(f"Path: {path}: {excinfo[1]}")

def check_is_admin_rights():
    # type: () -> bool
    """Return True if user has admin privileges.

    Raises:
        AdminStateUnknownError if user privileges cannot be determined.
    """
    try:
        return os.getuid() == 0
    except AttributeError:
        pass
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except AttributeError:
        raise AdminStateUnknownError


def clear_dir_per_file(start_path, config=None, log_delete_error=True):
    base_config = {
        # 'clear_dir_per_file': {'examples':  {
        #                       'include': (),
        #                       'exclude': (),},
        #               }

        'clear_dir_per_file': {
        },
    }
    if config:
        base_config.update(config)
    clear_dirs = base_config.get('clear_dir_per_file', {})
    size_report = config.get('size_report', False)

    for dir_name, attributes in clear_dirs.items():
        dir_path = os.path.join(start_path, dir_name)
        info(f'Clear clear_one_dir_per_file: {dir_path}')
        include_masks = attributes.get('include', ())
        exclude_masks = attributes.get('exclude', ())
        clear_one_dir_per_file(dir_path, exclude_masks, include_masks, size_report)


def clear_one_dir_per_file(start_path, exclude_mask=(), include_mask=(), size_report=False):
    if size_report:
        info(f'{start_path}: {get_folder_size_h(start_path)}')
    for root, dir_names, file_names in os.walk(start_path):
        for file_name in file_names:
            work_path = os.path.join(root, file_name)
            try:
                if include_mask:
                    if any([PurePath(work_path).match(exp) for exp in include_mask]):
                        os.remove(work_path)
                elif not exclude_mask or not any([PurePath(work_path).match(exp) for exp in exclude_mask]):
                    os.remove(work_path)
            except PermissionError as pe:
                error(f'Permission Error {pe}')
            except Exception as e:
                exception(f'{work_path} - {e}')


def clear_dir_content(start_path, clean_dirs=True, clear_files=True, size_report=False, log_error=True):
    if size_report:
        info(f'{start_path}: {get_folder_size_h(start_path)}')
    try:
        root, dir_names, file_names = next(os.walk(start_path))
    except StopIteration:
        root = start_path
        dir_names = ()
        file_names = ()
    if log_error:
        operations = functools.partial(shutil.rmtree, ignore_errors=False, onerror=on_error)
    else:
        operations = functools.partial(shutil.rmtree, ignore_errors=True)
    if clean_dirs:
        for dir_name in dir_names:
            work_path = os.path.join(root, dir_name)
            if not check_work_in_temp(work_path):
                operations(work_path)
    if clear_files:
        for file_name in file_names:
            work_path = os.path.join(root, file_name)
            try:
                os.remove(work_path)
            except PermissionError as pe:
                error(f'Permission Error {pe}')
            except Exception as e:
                exception(f'{work_path} - {e}')
    if size_report:
        info(f'{start_path}: {get_folder_size_h(start_path)}')


def clear_recycle_bins(log_error=True):
    if log_error:
        operations = functools.partial(shutil.rmtree, ignore_errors=False, onerror=on_error)
    else:
        operations = functools.partial(shutil.rmtree, ignore_errors=True)
    if check_is_admin_rights():
        for drive in get_fixed_drives():
            operations(f'{drive}:\\$Recycle.Bin')
        return True
    else:
        return False


def get_users_dir():
    return Path(os.path.expanduser('~')).parent


def work_on_user_folders(path, cmd: Callable = print, config=None, exclude=(), include=()):
    result = {}
    for user_name in os.listdir(path):
        full_path = os.path.join(path, user_name)
        try:
            if include:
                process = (os.path.isdir(full_path) and user_name in include)
            else:
                process = (os.path.isdir(full_path) and user_name not in exclude)

            if process:
                result[user_name] = cmd(full_path, user_name, config)
        except PermissionError:
            result[user_name] = False, 'Access Denied'


def clean_dir(path_base, full_clean, only_sub_dir, size_report=False, log_error=True):
    if size_report:
        info(f'{path_base}: {get_folder_size_h(path_base)}')
    if os.path.exists(path_base) and os.path.isdir(path_base):
        for d in os.listdir(path_base):
            process_path = os.path.join(path_base, d)
            info(f'Clear dir: {process_path}')
            if os.path.isdir(process_path):
                if d in full_clean:
                    clear_dir_content(process_path, size_report=False, log_error=log_error)
                elif d in only_sub_dir:
                    clear_dir_content(process_path, clear_files=False, size_report=False, log_error=log_error)
        if size_report:
            info(f'{path_base}: {get_folder_size_h(path_base)}')


def clear_inetcache(user_path, config=None, log_delete_error=True):
    base_config = {
        'full_clear_dirs': ('Content.MSO', 'Content.Word'),
        'only_sub_dirs': ('Content.Outlook', 'IE')
    }
    if config:
        base_config.update(config)

    size_report = base_config.get('size_report', False)
    work_path = os.path.join(user_path, r'AppData\Local\Microsoft\Windows\INetCache')
    info(f'Clear inet cache dir: {work_path}')
    clean_dir(work_path, config.get('full_clear_dirs', ()), base_config.get('only_sub_dirs', (), ),
              size_report=size_report, log_error=log_delete_error)


def cleanup_user_folder(user_path, config: dict = None, log_delete_error=True):
    base_config = {
        'user_folders_cleanup': (),
    }
    if config:
        base_config.update(config)
    size_report = config.get('size_report', False)
    for dir_name in base_config.get('user_folders_cleanup', ()):
        work_dir = os.path.join(user_path, dir_name)
        info(f'Clear user dir content: {work_dir}')
        clear_dir_content(work_dir, size_report=size_report, log_error=log_delete_error)


def cleanup_user_temp_folder(user_path, config: dict = None):
    base_config = {
        'user_temp_folders_cleanup': (r'AppData\Local\Temp',),
    }
    if config:
        base_config.update(config)
    size_report = config.get('size_report', False)
    log_error = config.get('loging_delete_error', True)
    for dir_name in base_config.get('user_temp_folders_cleanup', ()):
        work_dir = os.path.join(user_path, dir_name)
        info(f'Clear User Temp dir: {work_dir}')
        clear_dir_content(work_dir, size_report=size_report, log_error=log_error)


def clear_system(config: dict = None):
    base_config = {
        'system_dirs': ('Windows\\Temp', r'Windows\SoftwareDistribution'),
    }
    if config:
        base_config.update(config)
    size_report = config.get('size_report', False)
    system_drive = get_system_drive()
    for dir_name in base_config.get('system_dirs', ()):
        work_path = os.path.join(system_drive, dir_name)
        info(f'Clear System dir: {work_path}')
        clear_dir_content(work_path, size_report=size_report)


def get_folder_size(folder):
    return sum(file.stat().st_size for file in Path(folder).rglob('*'))


def get_folder_size_h(folder):
    return format_space(get_folder_size(folder))


def get_system_drive():
    system_path = win32api.GetSystemDirectory()
    drive = Path(system_path).home().drive
    return drive + '\\' if drive[-1] != '\\' else drive


def get_system_drive_space():
    return disk_space()


def format_space(space):
    abs_space = abs(space)
    if abs_space < 1024:
        return f'{space}b'
    elif 1024 <= abs_space < (1024 ** 2):
        return f'{space // 1024}Kb'
    elif (1024 ** 2) <= abs_space < (1024 ** 3):
        return f'{space // (1024 ** 2)}Mb'
    elif (1024 ** 3) <= abs_space < (1024 ** 4):
        return f'{space // (1024 ** 3)}Gb'
    elif (1024 ** 4) <= abs_space < (1024 ** 5):
        return f'{space // (1024 ** 3)}Tb'
    else:
        return f'{space // (1024 ** 4)}Pb'


def format_drive_info(total, used, free):
    total_formated = format_space(total)
    used_formated = format_space(used)
    free_formated = format_space(free)
    used_percent = f'{((used / total) * 100):.2f}'
    return f'Total={total_formated} Use={used_formated} Free={free_formated} Used={used_percent}%'


def dir_size(path_dir):
    size = 0
    for path, dirs, files in os.walk(path_dir):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size


def clean_user_folder_complex(full_path, user_name, config):
    operations_config = {
        'full_clear_dirs': config.get('full_clear_dirs', ()),
        'only_sub_dirs': config.get('only_sub_dirs', ()),
        'user_folders_cleanup': config.get('user_folders_cleanup', ()),
        'user_temp_folders_cleanup': config.get('user_temp_folders_cleanup', ()),
        'clear_dir_per_file': config.get('clear_dir_per_file', {}),
    }
    if 'user_config' in config and user_name in config['user_config']:
        operations_config.update(config['user_config'][user_name])
    logging_error = config.get('loging_delete_error', True)
    clear_inetcache(full_path, operations_config, log_delete_error=logging_error)
    cleanup_user_folder(full_path, operations_config, log_delete_error=logging_error)
    cleanup_user_temp_folder(full_path, operations_config)
    clear_dir_per_file(full_path, config, log_delete_error=logging_error)


def clean_users_data(config=None):
    user_dirs = get_users_dir()
    exclude = config.get('exclude', ())
    include = config.get('include', ())
    work_on_user_folders(user_dirs, clean_user_folder_complex,
                         exclude=exclude, include=include, config=config)


def clean_procedure(config=None):
    init_sys_disk = get_system_drive_space()
    info(format_drive_info(*init_sys_disk))
    clean_users_data(config)
    clear_recycle_bins(config.get('loging_delete_error', True))
    if config.get('system_temp', True):
        clear_system(config=config)
    if config.get('system_clean', False):
        if not system_dick_cleanup():
            warning('Cleanup process terminated with 120s timeout')
    final_sys_disk = get_system_drive_space()
    info(format_drive_info(*final_sys_disk))
    space_free = final_sys_disk[2] - init_sys_disk[2]  # this is free space, that grow after cleaning
    info(f'DISK Cleaned: {format_space(space_free)}')
    report_to_server(message=f'Cleaned: {format_space(space_free)} Free Space After {format_space(final_sys_disk[2])}',
                     config=config)
    stop_process = config.get('stop_process', None)
    can_reboot = True
    if stop_process:
        if not kill_control(stop_process):
            can_reboot = False
            error(f'Can`t stop process:{stop_process}')
    buffer = config.get('buffer_to_log', None)
    if buffer:
        if config.get('mail_report', True):
            if config.get('mail_error_only', True):
                if IS_ERROR_LOGGED:
                    send_mail_ex(message=buffer.getvalue(), config=config)
            else:
                send_mail_ex(message=buffer.getvalue(), config=config)

    if config.get('reboot', True) and can_reboot:
        time = config.get('reboot_after', 120)
        reboot(time=time)


if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config', default='clear_config.json')
    parser.add_argument('-sc', dest='system_clean', action='store_false')
    parser.add_argument('-ns', dest='dont_reboot', action='store_true')

    arguments = parser.parse_args()
    config = get_config(arguments.config, exit_on_error=False)
    if not config:
        config = {
            "token_url": r"https://inventory0201.bs.local.erc/token",
            "special_url": r"https://inventory0201.bs.local.erc/special",
            "proxy": r"http://fw01.bs.local.erc:8080/",
            "from_mail": "Department_BSP@erc.ua",
            "to_mail": "Department_BSP@erc.ua",
            "server": "WEBLOCAL0201.local.erc",
            "port": 25,
            'full_clear_dirs': ('Content.MSO', 'Content.Word'),
            'only_sub_dirs': ('Content.Outlook', 'IE'),
            'user_temp_folders_cleanup': (r'AppData\Local\Temp',),
            'user_folders_cleanup': (),
            'system_dirs': ('Windows\\Temp', r'Windows\SoftwareDistribution'),
            'report': True,
            'log_file': 'clear_profile.log',
            'log_level': 'info',
            'send_report_code': 15,
            'buffer_logging': True
        }
    if arguments.system_clean:
        config['system_clean'] = True
    if arguments.dont_reboot:
        config['reboot'] = False

    setup_logger(config)
    clean_procedure(config)

# print(format_drive_info(*get_system_drive_space()))
# dirs = get_users_dir()
# print(dirs)
# work_on_user_folders(dirs)
# work_on_user_folders(dirs, exclude='Default')
# work_on_user_folders(dirs, include='Default')
# clear_inetcache(r'C:\Users\User', 'User', None)
# cleanup_user_folder(r'C:\Users\User')
# clear_recycle_bins(True)
#
# print(win32api.GetDomainName())
#
# print(format_drive_info(*get_system_drive_space()))
# reboot(time=360)
# time.sleep(10)
# cancel_shutdown()
# a, b, c, d = win32api.GetDiskFreeSpace('c:\\')
# print(a * b * c, a * b * d)
# a, b, c, d = win32api.GetDiskFreeSpace('d:\\')
# print(a * b * c, a * b * d)
# print(format_drive_info(*disk_space('c:')))
# print(format_drive_info(*disk_space('d:')))
# print(format_drive_space(dir_size(r'c:\Users\User\AppData\Local\Temp')))
# print(format_drive_space(dir_size(r'c:\Temp')))
# rep = Report()
# clear_system_temp(config=None, report=rep)
# rep.print()
# print(format_drive_space(dir_size(r'c:\Temp')))
# rep = Report()
# clear_dir_content(r'c:\Users\User\AppData\Local\Temp', report=rep)
# rep.print()
    th.join()