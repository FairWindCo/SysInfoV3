import logging

import wmi

from fw_windows_sys_info.tools import clear_name


def form_soft(name, ver, install):
    # return clear_name(name, ver), ver, datetime.strptime(install, '%Y%m%d') if install else None
    return clear_name(name, ver), ver, install


def get_wmi_soft(wmi_obj=None):
    try:
        if not wmi_obj:
            wmi_obj = wmi.WMI()
        return [form_soft(mo.Name, mo.Version, mo.InstallDate) for mo in wmi_obj.Win32_Product()]
    except Exception:
        logging.error("ERROR", exc_info=True)
    return []
