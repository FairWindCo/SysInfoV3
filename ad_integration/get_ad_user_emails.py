import argparse
import platform
from typing import List

import dns
import ldap3
import ms_active_directory
from dns.rdatatype import RdataType
from ldap3 import Server
from ms_active_directory import ADDomain, configure_log_level
from ms_active_directory.environment.discovery.discovery_constants import DNS_TIMEOUT_SECONDS
from ms_active_directory.environment.discovery.discovery_utils import logger, \
    discover_ldap_domain_controllers_in_domain, discover_kdc_domain_controllers_in_domain
from ms_active_directory.logging_utils import enable_logging

from fw_automations_utils.clear_temp_folder import cleanup_mei


def _resolve_record_in_dns(record_name: str, record_type: RdataType, dns_nameservers: List[str], source_ip: str):
    """ Take a record and record type and resolve it in DNS.

    Returns a list of tuples where each tuple is in the format (host, port, priority, weight)
    sorted by priority and then weight.
    """
    temp_resolver = dns.resolver.Resolver()
    temp_resolver.timeout = DNS_TIMEOUT_SECONDS
    temp_resolver.lifetime = DNS_TIMEOUT_SECONDS
    if dns_nameservers:
        logger.debug('Using the following nameservers for dns lookup instead of the default system ones %s',
                     dns_nameservers)
        temp_resolver.nameservers = dns_nameservers
    # DNS queries are normally UDP. However, the best practices from microsoft for DNS are that
    # you use TCP if your result will be greater than 512 bytes. It states that DNS may truncate
    # results greater than 512 bytes.
    # If a record maps to a lot of results (like a service record for a large domain) then our
    # result can easily exceed 512 bytes, so we use tcp directly for lookups here, rather than
    # wait for udp to fail and then fallback.
    try:
        print(record_name, record_type, source_ip)
        resolved_records = temp_resolver.resolve(record_name, record_type, tcp=False,
                                                 source=source_ip)
    except dns.exception.DNSException as dns_ex:
        logger.info('Unable to query DNS for record %s due to: %s', record_name, dns_ex)
        print(dns_ex)
        return []
    except Exception as ex:
        logger.warning('Unexpected exception occurred when querying DNS for record %s: %s',
                       record_name, ex)
        print(ex)
        return []

    # turn our DNS records into more manageable tuples in the form:
    # (URI, Port, Priority, Weight)
    record_tuples = [(record.target.to_text(omit_final_dot=True), record.port, record.priority, record.weight)
                     for record in resolved_records]
    # A lower priority value (closer to 0) means that a record should be preferred.
    # Weight is used to rank order records of equal priority, and a higher value weight (further
    # above 0) means that a record should be preferred.
    # So we sort ascending, first by priority, and then by -1 * weight
    record_tuples = sorted(record_tuples, key=lambda record_tuple: (record_tuple[2], -1 * record_tuple[3]))
    logger.debug('Records returned in %s lookup for %s ordered by priority and weight: %s',
                 record_type, record_name, record_tuples)
    return record_tuples


def get_domain_session(domain_name, ldap_servers=None, kerberos_servers=None,
                       auth_method='NTLM', user_name=None, password=None):
    domain = ADDomain(domain_name, auto_configure_kerberos_client=auto_config,
                      ldap_servers_or_uris=ldap_servers, kerberos_uris=kerberos_servers)
    if arguments.debug:
        configure_log_level("DEBUG")
        enable_logging()
    # dns = ['10.241.24.25', '10.225.24.25', '10.253.24.28']
    ms_active_directory.environment.discovery.discovery_utils._resolve_record_in_dns = _resolve_record_in_dns
    print('AUTO_SEARCH', discover_ldap_domain_controllers_in_domain(domain_name))
    print('AUTO_SEARCH', discover_kdc_domain_controllers_in_domain(domain_name))
    ldap_servers = domain.get_ldap_servers()
    if not ldap_servers:
        ldap_servers = domain.get_ldap_uris()
    kerberos_servers = domain.get_kerberos_uris()
    if not ldap_servers:
        domain.refresh_ldap_server_discovery()
        ldap_servers = domain.get_ldap_uris()
    if not kerberos_servers:
        domain.refresh_kerberos_server_discovery()
        kerberos_servers = domain.get_kerberos_uris()
    # when using kerberos auth, the default is to use the kerberos
    # credential cache on the machine, so no password is needed
    computer_name = platform.node()
    if arguments.debug:
        print(f"DOMAIN: {domain}")
        print(f"NODE: {computer_name}")
        print(f"LDAP:{ldap_servers}")
        print(f"KERB: {kerberos_servers}")
        print(f"AUTH_MOD: {auth_method}")

    if user_name:
        session = domain.create_session_as_user(user=user_name, password=password,
                                                authentication_mechanism=auth_method)
    else:
        session = domain.create_session_as_computer(computer_name, authentication_mechanism=auth_method)
    return session


if __name__ == "__main__":
    cleanup_mei()
    parser = argparse.ArgumentParser()
    parser.add_argument('name', action='store')
    parser.add_argument('-d', '--domain', action='append', default=['bs.local.erc', 'local.erc'])
    parser.add_argument('-l', '--ldap', action='append', default=['10.225.24.28', '10.241.24.28', '10.253.24.25'])
    parser.add_argument('-k', '--kerberos', action='append')
    parser.add_argument('-a', '--attribute', action='append')
    parser.add_argument('--config_kerberos', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--print', action='store_true')
    parser.add_argument('-u', '--user', action='store')
    parser.add_argument('-p', '--password', action='store')
    parser.add_argument('-m', '--auth_method', action='store', default='NTLM', choices=(
        'GSSAPI', 'NTLM', 'SASL', 'SIMPLE', 'ANONYMOUS', 'PLAIN', 'DIGEST-MD5', 'EXTERNAL', 'KERBEROS'))
    arguments = parser.parse_args()
    domain_names = arguments.domain
    ldap_servers = None
    found_users = []
    if arguments.ldap:
        ldap_servers = [Server(ldap_url, mode=ldap3.IP_V4_ONLY) for ldap_url in arguments.ldap]
    kerberos_servers = arguments.kerberos
    user_name = arguments.user
    password = arguments.password
    auth_method = arguments.auth_method

    auto_config = arguments.config_kerberos
    sessions = [get_domain_session(domain_name, ldap_servers, kerberos_servers, auth_method, user_name, password)
                for domain_name in domain_names]

    arguments_set = {'mail'}
    if arguments.attribute:
        arguments_set.update(arguments.attribute)
    users_account_names = arguments.name.split(';')
    for user_account_name in users_account_names:
        for session in sessions:
            if session and session.is_open():
                user = session.find_user_by_sam_name(user_account_name, list(arguments_set))
                if user:
                    found_users.append(user)
                else:
                    print(f"{user_account_name}@{session.domain.domain}- NOT FOUND")
    if not found_users:
        print("WARNING: NO USERS FOUND")
    else:
        mails = []
        for user in found_users:
            if arguments.print:
                print(user.distinguished_name)
                print(user.get('cn'))
                print(user.get('sAMAccountName'))
                if arguments_set:
                    for a_name in arguments_set:
                        print(f'{a_name}:{user.get(a_name)}')
            find_mail = user.get('mail')
            if find_mail:
                mails.append(find_mail)
        print(';'.join(mails))
