import subprocess
import winreg

from fw_automations_utils.clear_temp_folder import cleanup_mei


def list_installed_soft():
    res = subprocess.run(["wmic.exe", "product", "get", "description"], stdout=subprocess.PIPE, encoding='cp1251')
    print(res.returncode)
    if res.returncode == 0:
        return [line.strip() for line in res.stdout.split('\n')[1:] if line]
    else:
        return None


def uninstall_soft(name):
    res = subprocess.run(['wmic', 'product', 'where', f'description="{name}"', 'uninstall'])
    return True if res.returncode == 0 else False


def delete_sub_key(root, sub):
    try:
        open_key = winreg.OpenKey(root, sub, 0, winreg.KEY_ALL_ACCESS)
        num, _, _ = winreg.QueryInfoKey(open_key)
        for i in range(num):
            child = winreg.EnumKey(open_key, 0)
            delete_sub_key(open_key, child)
        try:
            winreg.DeleteKey(open_key, '')
            return None
        except Exception as e:
            # log deletion failure
            return 'DELETE ERROR:' +str(e)
        finally:
            winreg.CloseKey(open_key)
    except Exception as e:
        return 'OPEN ERROR:' +str(e)

# log opening/closure failure
def delete_keys():
    keys_for_delete = [
        (winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Classes\\Installer\\Features\\38BDF3FD81AB967408AC7D7BE7F2A453'),
        (winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Classes\\Installer\\Products\\38BDF3FD81AB967408AC7D7BE7F2A453'),
        (winreg.HKEY_CLASSES_ROOT, 'Installer\\Products\\38BDF3FD81AB967408AC7D7BE7F2A453'),
    ]
    error_list = []
    for root, key in keys_for_delete:
        result = delete_sub_key(root, key)
        error_list.append(f'{key}: {result if result else "DELETED"}')
    return error_list

if __name__ == "__main__":
    cleanup_mei()
    list_soft = list_installed_soft()
    if list_soft is not None:
        zabbix_name = None
        for name in list_soft:
            if name.upper().startswith('ZABBIX'):
                zabbix_name = name
                break
        if zabbix_name:
            uninstall_soft(zabbix_name)
        else:
            print("ZABBIX not found")
        print('\n'.join(delete_keys()))
    else:
        print("LIST SOFT ERROR")

# Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Installer\Products\898A30537D970B240AACF1C6D070F3E4
# HKEY_CLASSES_ROOT\Installer\Products\38BDF3FD81AB967408AC7D7BE7F2A453
# HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Installer\Features\38BDF3FD81AB967408AC7D7BE7F2A453
# HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Installer\Products\38BDF3FD81AB967408AC7D7BE7F2A453