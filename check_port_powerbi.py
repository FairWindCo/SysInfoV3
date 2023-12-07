#pyinstaller --noconfirm --onefile --console --add-data "C:/Program Files/MIT/Kerberos/bin;bin/"  --hidden-import "sspilib.raw._text" --hidden-import "sspilib" "C:\Users\User\PycharmProjects\SysInfoV3\check_port_powerbi.py"
import argparse
import socket

import requests
from requests_kerberos import HTTPKerberosAuth
from requests_ntlm import HttpNtlmAuth
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from fw_automations_utils.clear_temp_folder import cleanup_mei_threading


def check_web_access(server, port, url, proxy_server, user, password, use_kerberos=False, debug=False):
    if use_kerberos:
        a = "KERB"
        basic = HTTPKerberosAuth()
    elif user:
        a = "NTLM"
        basic = HttpNtlmAuth(user, password)
    else:
        a = "No"
        basic = None
    if proxy_server:
        proxy = {
            'http': proxy_server,
            'https': proxy_server
        }
    else:
        proxy = None
    link = f'{a} https://{server}:{port}/'
    proxy_name = f' with proxy {proxy_server}' if proxy_server else 'no proxy'
    try:
        response = requests.get(
            link,
            auth=basic, verify=False,
            proxies=proxy)
        code = response.status_code
        if code == 200:
            print(f'CONNECT TO {link}  {proxy_name} - OK')
        elif code == 404:
            print(f'CONNECT TO {link} {proxy_name} - OK but resource not found {code}')
        elif code == 401:
            print(f'CONNECT TO {link} {proxy_name} - OK but user not authorized {code}')
        elif code == 403:
            print(f'CONNECT TO {link} {proxy_name} - OK but access denied {code}')
        elif 300 <= code <= 302:
            print(f'CONNECTED TO {link} {proxy_name} - OK with REDIRECT {code}')
        elif 500 <= code < 600:
            print(f'CONNECTED TO {link} {proxy_name} - OK but server error {code}')

        else:
            print(f'CONNECTED TO {link} {proxy_name} - SUCCESS BY WITH CODE: {code}')
    except requests.exceptions.RequestException as e:
        if debug:
            print(e)
        print(f'CONNECT TO {link} {proxy_name} - FAIL')


if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser(
        prog='Check port',
        description='Script to check port with selected source')
    parser.add_argument('-s', '--server', default='pbirs0001.local.erc')
    parser.add_argument('-p', '--port', default=443)
    parser.add_argument('-t', '--url',
                        default='reports/browse')
    parser.add_argument('-a', '--proxy1', default='http://fw01.bs.local.erc:8080/')
    parser.add_argument('-b', '--proxy2', default='http://fw02.bs.local.erc:8080/')
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--kerberos', action='store_false')
    parser.add_argument('-d', '--debug', action='store_true')
    parsed_arg = parser.parse_args()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((parsed_arg.server, int(parsed_arg.port)))
        s.close()
        print(f'CONNECT TO TCP {parsed_arg.server}:{parsed_arg.port} - SUCCESS')
    except OSError as e:
        if parsed_arg.debug:
            print(e)
        print(f'CONNECT TO {parsed_arg.server}:{parsed_arg.port}  - FAIL')
    print("TRY WEB ACCESS to url:"+parsed_arg.url)
    check_web_access(parsed_arg.server, parsed_arg.port,
                     parsed_arg.url, None,
                     parsed_arg.user, parsed_arg.password,parsed_arg.kerberos,parsed_arg.debug
                     )
    check_web_access(parsed_arg.server, parsed_arg.port,
                     parsed_arg.url,  parsed_arg.proxy1,
                     parsed_arg.user, parsed_arg.password,parsed_arg.kerberos,parsed_arg.debug
                     )
    check_web_access(parsed_arg.server, parsed_arg.port,
                     parsed_arg.url, parsed_arg.proxy2,
                     parsed_arg.user, parsed_arg.password,parsed_arg.kerberos,parsed_arg.debug
                     )

    th.join()
