import logging

import wmi


def get_system_info(wmi_obj=None):
    objects_names = [
        "Win32_OperatingSystem",
        "Win32_ComputerSystem",
        "Win32_DiskDrive",
        "Win32_Processor",
        "Win32_PerfRawData_Counters_HyperVDynamicMemoryIntegrationService"
    ]
    result = {}
    if not wmi_obj:
        wmi_obj = wmi.WMI()

    try:
        for name in objects_names:
            result[name] = {
                'infos': [],
                'count': 0
            }
            logging.debug(name)
            mos = getattr(wmi_obj, name)
            count = 0
            for mo in mos():
                info = {}
                for prop in mo.properties:
                    val = getattr(mo, prop)
                    logging.debug(f"{name} = {prop}: {val}")
                    info[prop] = val
                result[name]['infos'].append(info)
                count += 1
            result[name]['count'] = count
    except Exception as e:
        logging.error(e, exc_info=True)
    return result


def get_hot_fix(wmi_obj=None):
    try:
        if not wmi_obj:
            wmi_obj = wmi.WMI()
        list_fix = [(
            mo.HotFixID,
            mo.InstalledOn
        ) for mo in wmi_obj.Win32_QuickFixEngineering()]
        logging.debug(list_fix)
        return list_fix
    except Exception as e:
        logging.error(e, exc_info=True)
    return []
