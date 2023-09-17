import platform

from fw_utils.utils import execute_os_command


def get_host_info():
    command = f'hostnamectl'
    result, _, info, err = execute_os_command(command, in_sudo=True)
    sys_info = {
        'host': platform.node(),
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
        system_info = {}
        lines = info.split('\n')
        print(lines)


if __name__ == "__main__":
    get_host_info()
