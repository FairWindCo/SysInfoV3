import datetime
import os

from fw_server_communications.encrypt.message_sign import extract_host_domain_name
from fw_utils.utils import execute_os_command


def extract_host_info(bytes_str: bytes):
    pos_delimenter = bytes_str.find(b':')
    if pos_delimenter:
        return bytes_str[pos_delimenter + 1:].strip().decode()
    else:
        return ''


def extract_create_file_time(path: str = '/', format='%d.%m.%Y %H:%M:%S'):
    if os.path.exists(path):
        time_stamp = os.stat('/').st_ctime
        date = datetime.datetime.fromtimestamp(time_stamp)
        return date.strftime(format)
    else:
        return ''


def get_host_info():
    command = f'hostnamectl'
    result, _, info, err = execute_os_command(command, in_sudo=True)
    host, domain = extract_host_domain_name()
    sys_info = {
        'host': host,
        'Domain': domain,
        # 'Model': info['Win32_ComputerSystem']['infos'][0]['Model'],
        # 'Domain': info['Win32_ComputerSystem']['infos'][0]['Domain'],
        # 'sysname': info['Win32_OperatingSystem']['infos'][0]['Caption'],
        # 'Manufacturer': info['Win32_ComputerSystem']['infos'][0]['Manufacturer'],
        # 'TotalPhysicalMemory': str(info['Win32_ComputerSystem']['infos'][0]['TotalPhysicalMemory']),
        # 'NumberOfProcessors': int(info['Win32_ComputerSystem']['infos'][0]['NumberOfProcessors']),
        # 'Version': info['Win32_OperatingSystem']['infos'][0]['Version'],
        # 'BuildNumber': info['Win32_OperatingSystem']['infos'][0]['BuildNumber'],
        # 'InstallDate': info['Win32_OperatingSystem']['infos'][0]['InstallDate'],
        # 'OSArchitecture': info['Win32_OperatingSystem']['infos'][0]['OSArchitecture'],
        # 'hdd_count': info['Win32_DiskDrive']['count'],
        # 'cpu_count': info['Win32_Processor']['count'],
        'hdd_info': [],
        'cpu_info': []

    }
    if result:
        lines = info.split(b'\n')
        if len(lines) > 10:
            sys_info['Manufacturer'] = extract_host_info(lines[9])
            sys_info['OSArchitecture'] = extract_host_info(lines[8])
            sys_info['Model'] = extract_host_info(lines[10])
            version = extract_host_info(lines[7])
            sys_info['Version'] = version[6:] if version.startswith('Linux') else version
            sys_info['sysname'] = extract_host_info(lines[6])
            sys_info['InstallDate'] = extract_create_file_time()
        print(lines)
    print(sys_info)
    return sys_info


if __name__ == "__main__":
    get_host_info()
