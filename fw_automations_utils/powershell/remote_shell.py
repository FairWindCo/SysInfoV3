import base64
import sys
from itertools import chain

from winrm import Protocol

from fw_automations_utils.automation.automation import Result
from fw_automations_utils.powershell.powershell import PowerShellRunner, PowerShellCommand


class RemotePowerShellRunner(PowerShellRunner):

    def __init__(self, host: str, use_http: bool = False, power_shell_path: str = None, logger_service=None):
        super().__init__(power_shell_path, logger_service)

        self.endpoint = f'http://{host}:5985/wsman' if use_http else f'https://{host}:5986/wsman'
        p = Protocol(
            endpoint=self.endpoint,
            transport='kerberos',
            server_cert_validation='ignore')
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
            cmd_str = ' '.join(cmd)
            bytes_cmd = bytes(chain.from_iterable([ch, 0] for ch in cmd_str.encode()))
            encoded_command = base64.b64encode(bytes_cmd).decode().replace('\n', '')
            shell_command = (self.power_shell_path, '-encodedCommand', encoded_command)
        else:
            shell_command = f'{self.power_shell_path} -Command "& {{{command}}}"'
        # command_id = self.protocol.run_command(self.session_id, self.power_shell_path, arguments=cmd,
        #                                        skip_cmd_shell=True)
        self.logger.debug(shell_command)
        command_id = self.protocol.run_command(self.session_id, shell_command)

        out, err, status_code = self.protocol.get_command_output(self.session_id, command_id)
        self.protocol.cleanup_command(self.session_id, command_id)

        out = out.decode(sys.stdout.encoding, 'replace')
        err = err.decode(sys.stdout.encoding, 'replace')

        self.logger.debug("Returned: \n\tout:[%s], \n\terr:[%s]" % (out, err))

        success = status_code == 0
        return Result(success, status_code, out, err)
