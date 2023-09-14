from subprocess import Popen, PIPE


def init_key(keytab_file: str = "/etc/krb5.keytab", user_realm: str = None):
    kinit_args = ['/usr/bin/kinit', '-kt', keytab_file]
    if user_realm:
        kinit_args.append(user_realm)
    subp = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    subp.wait()
