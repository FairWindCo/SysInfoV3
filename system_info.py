import argparse
import json
import logging
import os
import platform
import socket
from pprint import pprint

import win32timezone
import wmi

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading
from fw_automations_utils.config import get_config
from fw_automations_utils.logger_functionality import setup_logger
from fw_server_communications.inventory_communications import send_info
from fw_windows_sys_info.installed_future import get_wmi_futures
from fw_windows_sys_info.installed_soft import get_wmi_soft
from fw_windows_sys_info.service_info import get_services
from fw_windows_sys_info.system_info import get_system_info, get_hot_fix
from fw_windows_sys_info.taskscheduller import get_tasks

# clr.AddReference("System.ServiceProcess")
# for auto-py-to-exe DO NOT DELETE
win32timezone.SYSTEMTIME


def form_host_info_json(small_info=False):
    info = get_system_info()
    result = {
        'host': platform.node(),
    }
    if not small_info:
        logging.debug('TRY UPDATE INFO')
        result.update(
            {'SystemFamily': info['Win32_ComputerSystem']['infos'][0].get('SystemFamily',
                                                                          info['Win32_ComputerSystem']['infos'][0].get(
                                                                              'SystemType', 'Unknown')),
             'Model': info['Win32_ComputerSystem']['infos'][0]['Model'],
             'Domain': info['Win32_ComputerSystem']['infos'][0]['Domain'],
             'sysname': info['Win32_OperatingSystem']['infos'][0]['Caption'],
             'Manufacturer': info['Win32_ComputerSystem']['infos'][0]['Manufacturer'],
             'TotalPhysicalMemory': str(info['Win32_ComputerSystem']['infos'][0]['TotalPhysicalMemory']),
             'NumberOfProcessors': int(info['Win32_ComputerSystem']['infos'][0]['NumberOfProcessors']),
             'Version': info['Win32_OperatingSystem']['infos'][0]['Version'],
             'BuildNumber': info['Win32_OperatingSystem']['infos'][0]['BuildNumber'],
             'InstallDate': info['Win32_OperatingSystem']['infos'][0]['InstallDate'],
             'OSArchitecture': info['Win32_OperatingSystem']['infos'][0]['OSArchitecture'],
             'hdd_count': info['Win32_DiskDrive']['count'],
             'cpu_count': info['Win32_Processor']['count'],
             'hdd_info': [],
             'cpu_info': []
             }
        )
    logging.debug('TRY DISK INFO')
    for hdd_info in info['Win32_DiskDrive']['infos']:
        if hdd_info['Size'] is not None and int(hdd_info['Size']) > 0:
            logging.info(f"{hdd_info['Model']}, {hdd_info['Size']}")
            result['hdd_info'].append({
                'model': hdd_info['Model'],
                'size': int(hdd_info['Size'])
            })
    logging.debug('TRY PROC INFO')
    for cpu_info in info['Win32_Processor']['infos']:
        logging.debug(cpu_info)
        result['cpu_info'].append({
            'model': cpu_info['Name'],
            'ThreadCount': int(cpu_info['ThreadCount']) if cpu_info.get('ThreadCount') else 1,
            'NumberOfCores': int(cpu_info['NumberOfCores']),
        })
    if 'SystemFamily' not in result or result['SystemFamily'] is None:
        result['SystemFamily'] = ''
    virtualisator_mem = info['Win32_PerfRawData_Counters_HyperVDynamicMemoryIntegrationService']

    if virtualisator_mem and len(virtualisator_mem['infos']):
        max_mem = int(virtualisator_mem['infos'][0]['MaximumMemoryMbytes']) * 1024 * 1024
        logging.info(f"HyperVDynamicMemory {max_mem}")
        result['CurrentTotalPhysicalMemory'] = result['TotalPhysicalMemory']
        result['TotalPhysicalMemory'] = max_mem
        result['IsVirtualMachine'] = True
    else:
        result['IsVirtualMachine'] = False

    logging.debug("END COMMON INFO")
    return result


def get_ip_list():
    return socket.gethostbyname_ex(socket.gethostname())[-1]


if __name__ == "__main__":
    # for soft in get_wmi_soft():
    #     print soft

    # # get_services()
    # tasks = get_tasks()
    # for task in tasks:
    #     print task['name'], task['task'], task['schedule']
    # exit()
    # tasks = get_tasks()
    # for task in tasks:
    #     print task['new_path']
    # exit()
    # get_tasks_info_xml()
    # exit()
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser()
    parser.add_argument('--soft', dest='soft', action='store_true')
    parser.add_argument('-i', dest='info', action='store_true')
    parser.add_argument('-f', dest='save')
    parser.add_argument('-l', dest='load')
    parser.add_argument('-c', dest='config', default='systeminfo_config.json')
    parser.add_argument('-p', dest='echo', action='store_true')
    parser.add_argument('-s', dest='skip', action='store_true')
    parser.add_argument('-r', dest='report', default=None)
    parser.add_argument('-d', dest='debug', default=None)
    parser.add_argument('--ignore_certificate', action="store_true")

    parser.add_argument('--show_dcom_tasks', action="store_true")
    parser.add_argument('--show_system_tasks', action="store_true")
    parser.add_argument('--show_hidden_tasks', action="store_true")
    parser.add_argument('--proxy', default=None)

    arguments = parser.parse_args()
    config = get_config(arguments.config, exit_on_error=False, default_config={
        "token_url": "https://inventory0201.bs.local.erc/token",
        "special_url": "https://inventory0201.bs.local.erc/host_info_update",
        "proxy": "http://fw01.bs.local.erc:8080/",
        "server": "web01.local.erc",
        "from_mail": "manenok@i.ua",
        "log_out": "True",
        "log_level": "info",
        "log_file": f".\\report_{platform.node()}.log"
    })
    if arguments.proxy:
        config['proxy'] = arguments.proxy

    if arguments.report:
        config['log_file'] = os.path.join(arguments.report, f'report_{platform.node()}.log')
    if arguments.debug:
        config['log_level'] = arguments.debug
    if arguments.ignore_certificate:
        config['ignore_certificate'] = True
    if arguments.show_dcom_tasks:
        config['show_dcom_tasks'] = arguments.show_dcom_tasks
    if arguments.show_system_tasks:
        config['show_system_tasks'] = arguments.show_system_tasks
    if arguments.show_hidden_tasks:
        config['show_hidden_tasks'] = arguments.show_hidden_tasks

    hide_dcom = not config.get('show_dcom_tasks', False)
    hide_system_tasks = not config.get('show_system_tasks', False)
    show_hide = config.get('show_hidden_tasks', False)

    setup_logger(config)


    if arguments.load:
        use_platform_host = False
        f = open(arguments.load, 'rt')
        try:
            json_str = f.read()
            info = json.loads(json_str)
        finally:
            f.close()

    else:
        use_platform_host = True
        logging.info("CHECK COMMON INFO")
        wmi_obj = wmi.WMI()
        if arguments.info:
            print(get_system_info(wmi_obj))
            print(get_services())
            print(get_tasks(show_hidden=show_hide, hide_dcom=hide_dcom, hide_system=hide_system_tasks))
            print(get_ip_list())
            exit(0)
        info = form_host_info_json(arguments.soft)
        logging.info("CHECK SERVICE INFO")
        info['services'] = get_services()
        logging.info("CHECK TASKS INFO")
        info['tasks'] = get_tasks(show_hidden=show_hide, hide_dcom=hide_dcom, hide_system=hide_system_tasks)
        logging.info("CHECK INSTALLED SOFT INFO")
        info['soft'] = [{
            'name': soft[0],
            'version': soft[1],
            'installed': soft[2]
        } for soft in get_wmi_soft(wmi_obj)]
        logging.info("CHECK IP INFO")
        info['ip'] = get_ip_list()
        logging.info("CHECK FUTURE INFO")
        info['futures'] = get_wmi_futures(wmi_obj)
        logging.info("CHECK HOTFIX INFO")
        info['hotfix'] = get_hot_fix(wmi_obj)

        if arguments.save:
            f = open(arguments.save, 'wt')
            try:
                f.write(json.dumps(info))
            finally:
                f.close()
    if not arguments.skip:
        res = send_info(info, config, use_platform_host)
        print(res)
    if arguments.echo:
        pprint(info)
    th.join()
