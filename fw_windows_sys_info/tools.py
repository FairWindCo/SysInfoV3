import re


def clear_name(name, ver):
    if name:
        if ver:
            # pattern = '[\\s]*[-]?[\\s]*' + ver
            pattern = r'[\s-]*' + ver + r'[.0-9\s]*'
            name = re.sub(pattern, '', name)
        name = name.replace('False', '').strip()
    return name


def get_display_name(parent_key, current_name):
    key = parent_key.OpenSubKey(current_name)
    if key:
        name = key.GetValue("DisplayName")
        ver = key.GetValue("DisplayVersion")
        installed = key.GetValue("InstallDate")
        if name:
            name = clear_name(name, ver)
        else:
            default_val = key.GetValue('')
            name = default_val if default_val else current_name
        return name, ver, installed
    else:
        return current_name, None, None


def list_sub_keys(key):
    if key:
        return [get_display_name(key, k) for k in key.GetSubKeyNames()]
    else:
        return []


def listing_sub_keys(key):
    if key:
        return key.GetSubKeyNames()
    else:
        return []


def convert_to_dict(info_list, info_dict=None):
    if info_dict is None:
        info_dict = {}
    if info_list:
        for info in info_list:
            info_dict[info[0]] = info
    return info_dict
