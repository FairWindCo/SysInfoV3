from __future__ import annotations

import base64
import json
import logging
import os
import platform
import sys
from datetime import datetime

from rsa import PublicKey, encrypt

from fw_server_communications.encrypt.default_key import load_key_default


def load_key(key_path):
    try:
        f = open(key_path, 'rb')
        try:
            key = f.read()
            return PublicKey.load_pkcs1(key)
        finally:
            f.close()
    except Exception as e:
        logging.critical('ERROR ' + str(e), exc_info=True)
        sys.exit(-2)


def extract_host_name(config=None):
    if config is None or config.get('dns_short_name', True):
        host, _ = extract_host_domain_name()
    else:
        host = platform.node()
    return host


def extract_host_domain_name(default_domain='bs.local.erc'):
    node_name = platform.node()
    point_index = node_name.find('.')
    if point_index > 0:
        host_name = node_name[:point_index]
        domain_name = node_name[point_index + 1:]
        return host_name, domain_name
    return node_name, default_domain


def encrypt_info_dict(info, config=None, use_platform_host=True, dump_dict=True):
    if config is None:
        config = {}
    PUBLIC_KEY_FILE = config.get('public_key', None)
    if PUBLIC_KEY_FILE and os.path.exists(PUBLIC_KEY_FILE) and os.path.isfile(PUBLIC_KEY_FILE):
        public_key = load_key(PUBLIC_KEY_FILE)
    else:
        public_key = load_key_default()
    if public_key:
        host = extract_host_name() if use_platform_host else info.get('host', '')
        key_info = host + datetime.now().strftime("%d%m%y%H%M%S")
        key = base64.b64encode(encrypt(key_info.encode(), pub_key=public_key))
        info['key'] = key.decode()
        logging.debug(info)

        mes = json.dumps(info) if dump_dict else info
        return mes
    return None
