import logging

import wmi


def get_wmi_futures(wmi_obj=None):
    try:
        if not wmi_obj:
            wmi_obj = wmi.WMI()
        return [mo.Name for mo in wmi_obj.Win32_ServerFeature()]
    except Exception:
        logging.error("ERROR", exc_info=True)
    return []
