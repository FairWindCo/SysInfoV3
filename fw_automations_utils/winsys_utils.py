import itertools
import os.path
import re
import shutil
import subprocess
import sys
import time
from pathlib import PurePath

import win32api
import win32file


def get_removable_drives():
    """Returns a list containing letters from removable drives"""
    drive_list = win32api.GetLogicalDriveStrings()
    drive_list = drive_list.split("\x00")[0:-1]  # the last element is ""
    return [letter[0] for letter in drive_list if win32file.GetDriveType(letter) == win32file.DRIVE_REMOVABLE]


def get_fixed_drives():
    """Returns a list containing letters from removable drives"""
    drive_list = win32api.GetLogicalDriveStrings()
    drive_list = drive_list.split("\x00")[0:-1]  # the last element is ""
    return [letter[0] for letter in drive_list if win32file.GetDriveType(letter) == win32file.DRIVE_FIXED]


def get_all_drives():
    """Returns a list containing letters from removable drives"""
    drive_list = win32api.GetLogicalDriveStrings()
    drive_list = drive_list.split("\x00")[0:-1]  # the last element is ""
    return [letter[0] for letter in drive_list]


def reboot(time=60, message='Цей  сервер буде перезаватажено через {}{}'):
    if message:
        if time < 60:
            submessage = message.format(time, 'сек.')
        else:
            submessage = message.format((time // 60), 'хв.')
        p = subprocess.run(['shutdown', '/r', '/t', str(time), '/c', submessage], shell=True, timeout=20)
    else:
        p = subprocess.run(['shutdown', '/r', '/t', str(time)], shell=True, timeout=20)
    return p.returncode == 0


def cancel_shutdown():
    p = subprocess.run(['shutdown', '/a'], shell=True, timeout=10)
    return p.returncode == 0


def system_dick_cleanup(timeout=120):
    p = subprocess.Popen(['cleanmgr.exe',
                          '/sagerun:255',
                          '/AUTOCLEAN',
                          # '/sageset:11',
                          # '/VERYLOWDISK',
                          # '/d',
                          ], shell=True)
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        kill_task_by_pids(p.pid)
        return False
    return p.returncode == 0


def disk_space(drive='/'):
    if drive != '/' and drive[-1] != '\\':
        drive += '\\'
    total, used, free = shutil.disk_usage(drive)
    return total, used, free


split_pattern = re.compile((r'[ ]+'))


def get_application_path():
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path


def get_work_in_temp(current_dir):
    PurePath(get_application_path())
    application_path = PurePath(get_application_path())
    if application_path.is_relative_to(current_dir):
        return application_path.parts[len(PurePath(current_dir).parts):][0]
    else:
        return None


def check_work_in_temp(current_dir):
    PurePath(get_application_path())
    application_path = PurePath(get_application_path())
    return application_path.is_relative_to(current_dir)


def search_task(task_name: str) -> list:
    prepared_name = task_name.lower()
    p = subprocess.run(['tasklist'], shell=True, stdout=subprocess.PIPE, encoding='cp866', timeout=20)
    if p.returncode == 0:
        return [int(line[1]) for line in
                filter(lambda a: len(a) > 2,
                       map(lambda l: split_pattern.split(l), p.stdout.split('\n')[3:]))
                if line[0].lower() == prepared_name]
    return []


def kill_task_by_name(task_name: str) -> bool:
    prepared_name = task_name.lower()
    p = subprocess.run(['taskkill', '/T', '/IM', prepared_name], shell=True, timeout=20)
    return p.returncode == 0


COLUMN_SPLITTER = re.compile('\s{2,}')


def _columns_rdp_convertor(line: str) -> dict:
    line_elements = COLUMN_SPLITTER.split(line.strip())
    return {
        'session_name': line_elements[0],
        'username': line_elements[1] if len(line_elements) > 3 else '---',
        'id': int(line_elements[2] if len(line_elements) > 3 else line_elements[1]),
        'state': line_elements[3] if len(line_elements) > 3 else line_elements[2],
        'device': line_elements[4] if len(line_elements) > 4 else 'local',
    }


def _columns_convertor(line: str) -> dict:
    line_elements = COLUMN_SPLITTER.split(line.strip())
    return {
        'username': line_elements[0],
        'session_name': line_elements[1] if len(line_elements) > 3 else '---',
        'id': int(line_elements[2] if len(line_elements) > 3 else line_elements[1]),
        'state': line_elements[3] if len(line_elements) > 3 else line_elements[2],
        'idle_time': line_elements[4] if len(line_elements) > 4 else '---',
        'logon_time': line_elements[5] if len(line_elements) > 5 else 'local',
    }


def _convert_mem(mem_info: str) -> int:
    line = mem_info.replace(',', '').replace('я', '').replace(' ', '').strip().upper()

    last_char = line[-1]
    if last_char == 'K' or last_char == 'К':
        return int(line[:-1]) * 1024
    elif last_char == 'M' or last_char == 'М':
        return int(line[:-1]) * 1024 ** 2
    elif last_char == 'G' or last_char == 'Г':
        return int(line[:-1]) * 1024 ** 3
    elif last_char.isdigit():
        return int(line)
    else:
        return int(line[:-1])


def _task_convertor(line: str) -> dict:
    line_elements = line.strip().split(',')
    return {
        'image': line_elements[0][1:-1],
        'pid': int(line_elements[1][1:-1]),
        'session_name': line_elements[2][1:-1],
        'session_num': int(line_elements[3][1:-1]),
        'mem': _convert_mem(line_elements[4][1:-1]),
        'status': line_elements[5][1:-1],
        'user_name': line_elements[6][1:-1],
        'cpu_time': line_elements[7][1:-1],
        'window': line_elements[8][1:-1],
    }


def list_RDP_logged_users() -> list:
    p = subprocess.run(['qwinsta'], shell=True, timeout=20, capture_output=True)
    if p.returncode == 0:
        return [_columns_rdp_convertor(line) for line in p.stdout.decode().split('\r\n')[1:] if line]
    else:
        return ()


def list_logged_users() -> list:
    p = subprocess.run(['quser'], shell=True, timeout=20, capture_output=True)
    if p.returncode == 0:
        return [_columns_convertor(line) for line in p.stdout.decode().split('\r\n')[1:] if line]
    else:
        return ()



def list_all_process_users() -> list:
    p = subprocess.run(['tasklist', '/v', '/FO', 'CSV'], shell=True, capture_output=True, encoding='cp1251')
    if p.returncode == 0:
        text = p.stdout
        return [_task_convertor(line) for line in text.split('\n')[1:] if line]
    else:
        return ()


def kill_task_by_pids(*task_pids) -> bool:
    if task_pids:
        tasks = itertools.chain(*zip(itertools.repeat('/PID'), map(str, task_pids)))
        p = subprocess.run(['taskkill', '/T', *tasks], shell=True, timeout=20)
        return p.returncode == 0
    else:
        return True


def kill_control(task_name: str, control_time=10) -> bool:
    pids = search_task(task_name)
    if pids:
        if kill_task_by_pids(*pids):
            time.sleep(control_time)
        control = search_task(task_name)
        if not control:
            return True
        return False
    else:
        return True


if __name__ == '__main__':
    print(kill_control('notepad.exe'))
