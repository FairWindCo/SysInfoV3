# pyinstaller --noconfirm --onefile --console --add-data "C:/Program Files/MIT/Kerberos/bin;bin/"  --hidden-import "sspilib.raw" "C:\Users\User\PycharmProjects\SysInfoV3\check_port_powerbi.py"

import argparse
import socket

from fw_automations_utils.clear_temp_folder import cleanup_mei_threading

if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser(
        prog='Check port',
        description='Script to check port with selected source')
    parser.add_argument('server')
    parser.add_argument('-p', '--port', default=80)
    parser.add_argument('-s', '--source')

    parsed_arg = parser.parse_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if parsed_arg.source:
            s.bind((parsed_arg.source, 0))
        # s.bind(('192.168.88.113', 0))
        s.connect((parsed_arg.server, int(parsed_arg.port)))
        print(s)
        s.close()
        print(f'CONNECT {parsed_arg.server}:{parsed_arg.port} FROM {parsed_arg.source} - SUCCESS')
    except OSError as e:
        print(s)
        print(e)
        print(f'CONNECT {parsed_arg.server}:{parsed_arg.port} FROM {parsed_arg.source}  - FAIL')
    th.join()
