from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from requests.auth import HTTPBasicAuth, AuthBase, HTTPDigestAuth
from requests_kerberos import HTTPKerberosAuth
from requests_ntlm import HttpNtlmAuth

from fw_server_communications.proxy_auth.kerberos_proxy_auth import HTTPAdapterWithProxyKerberosAuth
from fw_server_communications.proxy_auth.proxy_auth_sniplet import HTTPAdapterWithProxyDigestAuth, \
    HTTPSAdapterWithProxyDigestAuth


class ResponseStateRequest(Enum):
    OK = 0,
    COMMUNICATION_ERROR = 1,
    TIMEOUT = 2,
    RESPONSE_STATUS_ERROR = 3


class ServerRequestor:
    @staticmethod
    def get_auth(auth_type: str, user_login: Optional[str], password: Optional[str], **kwargs) -> AuthBase:
        auth = auth_type.upper()
        auth_data = None
        if auth == 'BASIC':
            auth_data = HTTPBasicAuth(user_login, password)
        elif auth == 'DIGIT':
            auth_data = HTTPDigestAuth(user_login, password)
        elif auth == 'NTLM':
            auth_data = HttpNtlmAuth(user_login, password)
        elif auth == 'KERBEROS':
            auth_data = HTTPKerberosAuth(**kwargs)
        return auth_data

    @staticmethod
    def setup_server_auth(session: requests.Session, config: dict) -> requests.Session:
        server_username = config.get('user', None)
        server_password = config.get('pass', None)
        server_auth_type = config.get('auth_type', 'basic')
        kerberos_params = config.get('kerberos_params', {})
        if server_username:
            session.auth = ServerRequestor.get_auth(server_auth_type, server_username, server_password,
                                                    **kerberos_params)
        return session

    @staticmethod
    def setup_server_proxy(session_for_config: requests.Session, config: dict) -> requests.Session:
        global_proxy_url = config.get('proxy', None)
        proxy_http_url = config.get('http_proxy', global_proxy_url)
        proxy_https_url = config.get('https_proxy', global_proxy_url)
        logging.debug("Try Get CSRF Token")
        proxy_settings = {
            'http': proxy_http_url,
            'https': proxy_https_url
        } if proxy_http_url or proxy_https_url else None
        if proxy_https_url == '-' and proxy_http_url == '-':
            proxy_settings = None
        logging.debug(proxy_settings)
        session_for_config.proxies = proxy_settings
        auth_method = config.get('proxy_auth_method', '').upper()
        if proxy_settings:
            if auth_method == 'DIGEST':
                if proxy_http_url:
                    session_for_config.mount('http', HTTPAdapterWithProxyDigestAuth())
                if proxy_https_url:
                    session_for_config.mount('https', HTTPSAdapterWithProxyDigestAuth())
            elif auth_method == 'KERBEROS':
                if proxy_http_url:
                    session_for_config.mount('http', HTTPAdapterWithProxyKerberosAuth())
                if proxy_https_url:
                    session_for_config.mount('https', HTTPAdapterWithProxyKerberosAuth())
        logging.debug(f'PROXY AUTH METHOD: {auth_method}')
        return session_for_config

    @staticmethod
    def setup_header(session_for_config: requests.Session, config: dict) -> requests.Session:
        headers = config.get('http_headers', {})
        if headers:
            for name, value in headers.items():
                logging.debug(f'set header: {name}:{value}')
                session_for_config.headers[name] = value
        return session_for_config

    @staticmethod
    def create_session(config: Optional[dict]):
        if not config:
            config = {}

        session = requests.Session()
        session = ServerRequestor.setup_server_auth(session, config)
        session = ServerRequestor.setup_server_proxy(session, config)
        return session

    @staticmethod
    def communicate_with_server(session: Optional[requests.Session],
                                url: str, message: Optional[dict | str],
                                config: Optional[dict], **kwargs
                                ) -> tuple:
        if not config:
            config = {}
        response_data = None
        if url:
            timeout = config.get('timeout', 15)
            ignore_certificate = config.get('ignore_certificate', True)
            logging.debug(f'timeout: {timeout}')
            logging.debug(f'ignore certificate: {ignore_certificate}')
            try:
                if session is None:
                    session = ServerRequestor.create_session(config)
                session = ServerRequestor.setup_header(session, config)
                session.verify = not ignore_certificate
                if message is None:
                    # if ignore_certificate:
                    #     with no_ssl_verification():
                    #         response = session.get(url=url, timeout=timeout, verify=ignore_certificate, **kwargs)
                    # else:
                    #     response = session.get(url=url, timeout=timeout, verify=ignore_certificate, **kwargs)
                    response = session.get(url=url, timeout=timeout, **kwargs)
                else:
                    # if ignore_certificate:
                    #     with no_ssl_verification():
                    #         response = session.post(url=url, json=message, timeout=timeout, verify=ignore_certificate,
                    #                                 **kwargs)
                    # else:
                    #     response = session.post(url=url, json=message, timeout=timeout, verify=ignore_certificate,
                    #                             **kwargs)
                    response = session.post(url=url, data=message, timeout=timeout, **kwargs)
                if response.status_code == 200:
                    return session, response, ResponseStateRequest.OK
                else:
                    logging.warning(f"RESPONSE CODE: {response.status_code}")
                    return session, response, ResponseStateRequest.RESPONSE_STATUS_ERROR
            except requests.ConnectTimeout:
                logging.info('Connect Timeout')
                return session, None, ResponseStateRequest.TIMEOUT
            except requests.URLRequired as e_url:
                logging.warning('WARNING URL' + str(e_url))
                response_data = e_url
            except requests.ConnectionError as e:
                logging.warning('Connection ERROR {}'.format(e))
                response_data = e
            except requests.RequestException as e:
                logging.warning('REQUEST ERROR {}'.format(e))
                response_data = e

            except Exception as ex:
                response_data = ex
                logging.error('WARNING ' + str(ex), exc_info=True)

        else:
            logging.error("URL not set, don`t now where is server?")
        return session, response_data, ResponseStateRequest.COMMUNICATION_ERROR

    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = config if config else {}
        self.session = self.create_session(self.config)

    def server_request(self, url: str, message: Optional[dict | str]) -> dict:
        selected_proxy = self.config.get('selected_proxy', None)
        round_robin_proxy = self.config.get('round_robin_proxy', None)
        auto_select_proxy = self.config.get('auto_select_proxy', True)
        if round_robin_proxy is None or selected_proxy:
            _, response, status = self.communicate_with_server(self.session, url, message, self.config)
            return {
                'response': response,
                'status': status,
            }
        else:
            logging.debug("SELECT PROXY")
            for proxy_url in round_robin_proxy:
                self.config['proxy'] = proxy_url
                self.config['http_proxy'] = proxy_url
                self.config['https_proxy'] = proxy_url
                self.setup_server_proxy(self.session, self.config)
                _, response, status = self.communicate_with_server(self.session, url, message, self.config)
                if status == ResponseStateRequest.TIMEOUT:
                    continue
                else:
                    logging.info(f'SELECT PROXY: {proxy_url}')
                    if auto_select_proxy:
                        self.config['selected_proxy'] = proxy_url
                    return {
                        'response': response,
                        'status': status,
                    }
            return {
                'response': None,
                'status': ResponseStateRequest.TIMEOUT,
            }

    def add_header_field(self, name, value):
        header_dict = self.config.get('http_headers', {})
        header_dict[name] = value
        self.config['http_headers'] = header_dict

    def request_with_csrf(self, url: str, message: Optional[dict | str]):
        csrf = self.config.get('csrf', None)
        csrf_url = self.config.get('token_url', None)
        header_field_name = self.config.get('csrf_header_field_name', 'X-CSRFToken')
        message_field_name = self.config.get('csrf_message_field_name', 'csrfmiddlewaretoken')
        use_csrf = self.config.get('use_csrf', True)
        use_header = self.config.get('use_csrf_header', True)
        use_message = self.config.get('use_csrf_message', True)

        if use_csrf:
            if not csrf:
                if csrf_url:
                    logging.debug(f"Try Get CSRF Token from {csrf_url}")
                    response = self.server_request(csrf_url, None)
                    if response['status'] == ResponseStateRequest.OK:
                        obj_dict = response['response'].json()
                        logging.debug(obj_dict)
                        csrf = obj_dict.get('csrf', None)
                        header_field_name = obj_dict.get('header_name', None)
                        self.config['csrf'] = csrf
                        self.config['csrf_header_field_name'] = header_field_name
                    else:
                        logging.error(f"ERROR GET TOKEN {response['status']}")
                else:
                    logging.error('NO URL FOR GET CSRF TOKEN!')
                    return {
                        'response': None,
                        'status': ResponseStateRequest.COMMUNICATION_ERROR,
                    }
            if csrf:
                logging.debug(csrf)
                if use_header:
                    self.add_header_field(header_field_name, csrf)
                if use_message and message and isinstance(message, dict):
                    message[message_field_name] = csrf
                logging.debug("Try Send Data after csrf")
                return self.server_request(url, message)
        else:
            logging.debug("Try Send Data without csrf")
            return self.server_request(url, message)
