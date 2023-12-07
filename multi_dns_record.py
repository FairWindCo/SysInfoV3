# pyinstaller --noconfirm --onefile --console --hidden-import "requests-credssp" --hidden-import "requests-ntlm" --hidden-import "requests-kerberos" --hidden-import "winkerberos"  --add-data "C:/Program Files/MIT/Kerberos/bin;bin/" "C:/Users/User/PycharmProjects/SysInfoV3/multi_dns_record.py"

import argparse
import fnmatch
import logging
import platform
import re
import sys

from windowsdnsserver.command_runner.powershell_runner import PowerShellRunner, PowerShellCommand
from windowsdnsserver.command_runner.runner import Result
from windowsdnsserver.dns.dnsserver import DnsServerModule
from windowsdnsserver.dns.record import RecordType
from winrm.protocol import Protocol

from fw_automations_utils.clear_temp_folder import cleanup_mei_threading
from fw_automations_utils.logger_functionality import setup_logger


# pyinstaller --noconfirm --onefile --console --add-data "C:/Program Files/MIT/Kerberos/bin;bin/" --hidden-import "winkerberos" "C:/Users/User/PycharmProjects/SysInfoV3/multi_dns_record.py"
# pip uninstall windowsdnsserver_py
# pip install git+https://github.com/FairWindCo/windowsdnsserver-py
class RemotePowerShellRunner(PowerShellRunner):

    def __init__(self, host: str, use_http: bool = False, power_shell_path: str = None, logger_service=None,
                 method=None, user=None, password=None):
        super().__init__(power_shell_path, logger_service)

        self.endpoint = f'http://{host}:5985/wsman' if use_http else f'https://{host}:5986/wsman'
        args = {
            'endpoint': self.endpoint,
            'transport': 'kerberos',
            # 'transport':'credssp',

            'server_cert_validation': 'ignore'
        }
        if method:
            args['transport'] = method
        if user:
            args['username'] = user
            args['password'] = '' if password is None else password
        p = Protocol(**args)
        self.logger.debug(f'endpoint: {self.endpoint}')
        self.protocol = p
        self.session_id = None

    def open_session(self):
        if self.session_id is None:
            self.session_id = self.protocol.open_shell()

    def close_session(self):
        if self.session_id:
            self.protocol.close_shell(self.session_id)
            self.session_id = None

    def run(self, command: PowerShellCommand) -> Result:
        cmd = command.build()
        self.logger.debug("Running: [%s]" % ' '.join(cmd))
        self.logger.debug('using default encoding: [%s]' % sys.stdout.encoding)

        if self.session_id is None:
            self.open_session()

        # prepare
        # system("powershell -command '<some commands> | ConvertFrom-Json | <other commands>' ");
        command = ' '.join(cmd)
        if self.encode_command:
            (_, ver, _) = platform.python_version_tuple()
            if int(ver) < 11:
                from base64 import encodestring
                encoded_command = encodestring(' '.join(cmd).encode()).decode()
            else:
                from base64 import encodebytes
                command_string = ' '.join(cmd).encode()
                buf = bytearray()
                for comand_byte in command_string:
                    buf.append(comand_byte)
                    buf.append(0)
                encoded_command = encodebytes(buf).decode().replace('\n', '')
            shell_command = (self.power_shell_path, '-encodedCommand', encoded_command)
        else:
            shell_command = f'{self.power_shell_path} -Command "& {{{command}}}"'
        # command_id = self.protocol.run_command(self.session_id, self.power_shell_path, arguments=cmd,
        #                                        skip_cmd_shell=True)
        self.logger.debug(shell_command)
        command_id = self.protocol.run_command(self.session_id, ' '.join(shell_command))

        out, err, status_code = self.protocol.get_command_output(self.session_id, command_id)
        self.protocol.cleanup_command(self.session_id, command_id)

        out = out.decode(sys.stdout.encoding, 'replace')
        err = err.decode(sys.stdout.encoding, 'replace')

        self.logger.debug("Returned: \n\tout:[%s], \n\terr:[%s]" % (out, err))

        success = status_code == 0
        return Result(success, status_code, out, err)


def print_records(records_list: list):
    for rec in records_list:
        print(rec.name, rec.type.value, rec.content, rec.ttl)


if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser()
    parser.add_argument('--zone', action='store', default='bs.local.erc')
    parser.add_argument('-t', '--template', action='store', default='repair{:02d}')
    parser.add_argument('--target', action='store', default='dev01.bs.local.erc')
    parser.add_argument('--server', action='store', default=None)
    parser.add_argument('--remote', action='store', default=None)
    parser.add_argument('--remote_http', action='store_true')
    parser.add_argument('-s', '--start_number', action='store', default=0, type=int)
    parser.add_argument('-c', '--count_number', action='store', default=8, type=int)
    parser.add_argument('--step_number', action='store', default=1, type=int)
    parser.add_argument('-d', '--debug', action='store', default='info')
    parser.add_argument('--user', action='store', default=None)
    parser.add_argument('--password', action='store', default=None)
    parser.add_argument('--method', action='store', default='kerberos', choices=['kerberos', 'credssp', 'ntlm'])

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--create', action='store_true')
    action.add_argument('--create_from_file', action='store')
    action.add_argument('--list', action='store_true')
    action.add_argument('--search', action='store', default=None)
    action.add_argument('--like', action='store', default=None)
    action.add_argument('--test_powershell', action='store_true', default=None)
    arguments = parser.parse_args()
    setup_logger({'log_level': arguments.debug})
    dns_service_arguments = {
        'logger_service': logging.getLogger(),
        'server': arguments.server
    }
    if arguments.remote:
        dns_service_arguments['runner'] = RemotePowerShellRunner(host=arguments.remote,
                                                                 use_http=arguments.remote_http,
                                                                 logger_service=dns_service_arguments['logger_service'],
                                                                 method=arguments.method,
                                                                 user=arguments.user,
                                                                 password=arguments.password
                                                                 )
    dns_server = DnsServerModule(**dns_service_arguments)
    if not dns_server.is_dns_server_module_installed():
        sys.exit(-1)
    zone = arguments.zone

    logging.debug(f'LOG LEVEL:{arguments.debug}')

    if arguments.create:
        start_number = arguments.start_number
        count = arguments.count_number
        step = arguments.step_number
        template = arguments.template
        target = arguments.target
        for index in range(start_number, count, step):
            new_name = template.format(index)
            if not dns_server.add_cname_record(zone=zone, alias_name=new_name, server_name=target):
                logging.error(f'ERROR while create new alias: {new_name} for {target} in zone: {zone}')
            else:
                logging.info(f'create new alias: {new_name} for {target} in zone: {zone}')
    elif arguments.create_from_file:
        target = arguments.target
        with open(arguments.create_from_file, 'rt') as f:
            for line in f.readlines():
                line = re.sub('[\n\r]', '', line)
                if not line or line.startswith('#'):
                    continue
                if line[0] == '=':
                    target = line[1:]
                else:
                    new_name = line.strip()
                    point_index = line.find('.')
                    if line.find('.'):
                        new_name = line[:point_index]
                    # print(f"new alias: {new_name} for {target} in zone: {zone}")
                    if not dns_server.add_cname_record(zone=zone, alias_name=new_name, server_name=target):
                        logging.error(f'ERROR while create new alias: {new_name} for {target} in zone: {zone}')
                    else:
                        logging.info(f'create new alias: {new_name} for {target} in zone: {zone}')
    elif arguments.list:
        lists = dns_server.get_dns_records(zone=zone, record_type=RecordType.CNAME)
        print_records(lists)
    elif arguments.search:
        lists = dns_server.get_dns_records(zone=zone, record_type=RecordType.CNAME, name=arguments.search)
        print_records(lists)
    elif arguments.like:
        lists = dns_server.get_dns_records(zone=zone, record_type=RecordType.CNAME)
        print_records(filter(lambda el: fnmatch.fnmatch(el.name, arguments.like), lists))
    elif arguments.test_powershell:
        if dns_service_arguments['runner']:
            command = PowerShellCommand('$PSVersionTable')
            result = dns_service_arguments['runner'].run(command)
            logging.error(result.out)
            logging.error(result.err)
        else:
            logging.error("NO REMOTE SHELL")
    th.join()
#RUN AS admin
#multi_dns_record.exe --create_from_file dev01_aliases_221123.txt
