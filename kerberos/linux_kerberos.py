from fw_utils.utils import execute_os_command


def init_key(keytab_file: str = "/etc/krb5.keytab", user_realm: str = None, in_sudo: bool = True):
    kinit_args = ['-kt', keytab_file]
    if user_realm:
        kinit_args.append(user_realm)
    result, *_ = execute_os_command('/usr/bin/kinit', *kinit_args, in_sudo=in_sudo)
    return result
