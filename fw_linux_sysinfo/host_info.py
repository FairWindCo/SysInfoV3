import datetime
import json
import logging
import os

from fw_automations_utils.logger_functionality import get_config_and_set_logger
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


def extract_modify_file_time(path: str = '/var/cache/apt/pkgcache.bin', format='%d.%m.%Y %H:%M:%S'):
    if os.path.exists(path):
        time_stamp = os.stat('/').st_mtime
        date = datetime.datetime.fromtimestamp(time_stamp)
        return date.strftime(format)
    else:
        return ''


def get_host_info():
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
    result, _, info, err = execute_os_command('hostnamectl', in_sudo=True)
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
            sys_info['LastUpdateCheck'] = extract_modify_file_time()
            sys_info['hotfix'] = [
                ('last', extract_modify_file_time('/var/lib/apt/extended_states')),
            ]

    else:
        logging.warning('GET HOST INFO ERROR:' + err)
    result, _, info, err = execute_os_command('lshw', '-json', in_sudo=True)
    if result:
        try:
            sysinfo = json.loads(info)
            for element in sysinfo["children"][0]['children']:
                sys_info['SystemFamily'] = " ".join([sysinfo["children"][0]["vendor"],
                                                     sysinfo["children"][0]["product"],
                                                     sysinfo["children"][0]["version"]])
                if element['id'].startswith('cpu'):
                    sys_info['cpu_info'].append({
                        'model': element['product'],
                        'NumberOfCores': element['configuration']['cores'],
                        'ThreadCount': element['configuration']['threads'],
                    })
                elif element['id'] == 'memory':
                    sys_info['TotalPhysicalMemory'] = element['size']
                elif element['class'] == 'storage':
                    for disk in element['children']:
                        if 'size' in disk:
                            sys_info['hdd_info'].append({
                                'model': disk['product'],
                                'size': disk['size'],
                            })
                    print(element)

            # print(sysinfo["children"][0])
            sys_info['NumberOfProcessors'] = len(sys_info['cpu_info'])
            sys_info['cpu_count'] = len(sys_info['cpu_info'])
            sys_info['hdd_count'] = len(sys_info['hdd_info'])
        except Exception as e:
            logging.error("LOAD SYS INFO ERROR:" + str(e))

    else:
        logging.warning('GET HW INFO ERROR:' + err)
    sys_info['services'] = []
    result, _, info, err = execute_os_command('service', '--status-all', in_sudo=True)
    if result:
        for line in info.split(b'\n'):
            data = line.strip()
            if data and data[2] == b'+':
                print(data)
                sys_info['services'].append(data[5:].strip().decode())

    else:
        logging.warning('GET SERVICE ERROR:' + err)
    logging.debug(sys_info)
    return sys_info


if __name__ == "__main__":
    default_config = {
        "special_url": "https://inventory0201.bs.local.erc/host_info_update",
        "token_url": "https://inventory0201.bs.local.erc/token",
        'log_level': 'DEBUG',
        'log_file': None,
    }
    config, log_file = get_config_and_set_logger('backup.json', exit_on_error=False,
                                                 default_config=default_config)

    try:
        sys_info = get_host_info()
    except Exception as e:
        logging.critical(f"Can`t get system info: {e}")
