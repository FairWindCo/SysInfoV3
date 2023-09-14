from __future__ import annotations

import base64
import json
import logging
import urllib.parse
from typing import Optional

import requests

from fw_server_communications.encrypt.message_sign import encrypt_info_dict


def comminicate(req, csrf, proxy=None, cookie=None, username=None, password=None,
                timeout=10, ignore_certificate=False):
    import urllib.request
    from urllib.error import HTTPError
    from urllib.error import URLError
    import ssl
    # post = urllib.urlencode(message).encode()
    if proxy:
        handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
        opener = urllib.request.build_opener(handler)
        urllib.request.install_opener(opener)
    if csrf:
        req.add_header('X-CSRFToken', csrf)
        req.add_header('HTTP_X_CSRFTOKEN', csrf)
    if username and password:
        base64string = base64.b64encode(f'{username}:{password}'.encode())
        req.add_header("Authorization", "Basic %s" % base64string)

    req.add_header('Cookie', 'csrftoken={}'.format(csrf) if cookie is None else cookie)
    try:
        if ignore_certificate:
            logging.info("IGNORE CERTIFICATE")
            scontext = ssl.SSLContext(ssl.PROTOCOL_TLS)
            scontext.verify_mode = ssl.VerifyMode.CERT_NONE
            response = urllib.request.urlopen(req, context=scontext, timeout=timeout)
        # response = urllib2.urlopen(req, timeout=timeout)
        else:
            response = urllib.request.urlopen(req, timeout=timeout)
        cookie = response.headers.get('Set-Cookie')
        text = response.read()
        return text, cookie
    except HTTPError as e:
        logging.warning('WARNING HTTP {} ERROR {} {}'.format(e.code, e, e.reason))
    except URLError as e_url:
        logging.warning('WARNING ' + str(e_url))
    except Exception as ex:
        logging.error('WARNING ' + str(ex), exc_info=True)
    return None, None


def send_request(message, url, csrf, proxy=None, cookie=None, username=None, password=None,
                 timeout=10, ignore_certificate=False):
    import urllib.request
    from urllib.error import URLError
    if message is None or not url:
        return
    if not message:
        raise ValueError('message is empty')
    try:
        post = urllib.parse.quote(message, safe="")
        logging.debug(f'URL:{url}')
        req = urllib.request.Request(url, post.encode())
        req.add_header("Content-Type", 'application/json')
        text, _ = comminicate(req, csrf, proxy, cookie, username, password, timeout, ignore_certificate)
    except URLError as e_url:
        logging.warning('WARNING ' + str(e_url))
        text = None
    return text


def get_request(url, proxy=None, username=None, password=None, timeout=10, ignore_certificate=False):
    import urllib.request
    from urllib.error import URLError
    cookie = None
    try:
        req = urllib.request.Request(url)
        text, cookie = comminicate(req, None, proxy, cookie, username, password, timeout, ignore_certificate)
        if text:
            obj_dict = json.loads(text)
        else:
            obj_dict = {}
    except URLError as e_url:
        logging.warning('WARNING ' + str(e_url))
        obj_dict = {}
    except Exception as e:
        logging.error('WARNING ' + str(e), exc_info=True)
        obj_dict = {}
    return obj_dict.get('csrf', None), cookie



def communicate_with_server(session, url:str, message:Optional[dict|str], config):
    if session is None:
        session = requests.Session()
        server_username = config.get('user', None)
        server_password = config.get('pass', None)
        server_auth_type = config.get('auth_type', 'basic')
        proxy = config.get('proxy', None)


def send_request_req(session, message, url, csrf, header_field_name='X-CSRFToken'):
    logging.debug(url, session.cookies.items(), session.proxies)
    message['csrfmiddlewaretoken'] = csrf
    cookies = dict()
    for key, name in session.cookies.items():
        cookies[key] = name
    logging.debug(cookies)
    try:
        response = session.post(url,
                                # data={
                                #     'csrfmiddlewaretoken': csrf
                                # },
                                json=message,
                                cookies=cookies,
                                headers={
                                    header_field_name: csrf
                                })
        return response.status_code, response.text
    except Exception as e:
        logging.critical('WARNING ' + str(e), exc_info=True)





def get_request_req(session, url):
    try:
        logging.debug(url, session.proxies, session.cookies)
        text = session.get(url, verify=False)
        if text.status_code == 200:
            obj_dict = text.json()
        else:
            obj_dict = {}
    except Exception as e:
        logging.error('WARNING ' + str(e), exc_info=True)
        obj_dict = {}
    return obj_dict.get('csrf', None), obj_dict.get('header_name', None)


def send_info_request_req(info, config=None, use_platform_host=True,
                          url_default='http://127.0.0.1:8000/host_info_update'):
    import requests
    if config is None:
        config = {}
    url_token = config.get('token_url', 'http://127.0.0.1:8000/token')
    url_special = config.get('special_url', url_default)
    proxy = config.get('proxy', None)
    logging.debug("Try Get CSRF Tolken")
    session = requests.Session()
    proxy_settings = {
        'http': proxy,
        'https': proxy} if proxy else None
    session.proxies = proxy_settings
    csrf, field_name = get_request_req(session, url_token)
    logging.debug(session.cookies.items())
    logging.debug(csrf)
    mes = encrypt_info_dict(info, config, use_platform_host, dump_dict=False)
    logging.debug("Try Send")
    logging.debug(mes)
    res = send_request_req(session, mes, url_special, csrf, header_field_name=field_name)
    logging.debug(res)
    return res


def send_info_request(info, config=None, use_platform_host=True,
                      url_default='http://127.0.0.1:8000/host_info_update'):
    try:
        if config is None:
            config = {}
        url_token = config.get('token_url', 'http://127.0.0.1:8000/token')
        url_special = config.get('special_url', url_default)

        username = config.get('user', None)
        password = config.get('pass', None)

        proxy = config.get('proxy', None)
        ignore_certificate = config.get('ignore_certificate', False)
        timeout = config.get('timeout', 15)
        logging.debug("Try Get CSRF Tolken")
        csrf, cookie = get_request(url_token, proxy=proxy,
                                   username=username, password=password, timeout=timeout,
                                   ignore_certificate=ignore_certificate)
        logging.debug(csrf)
        logging.debug(cookie)
        mes = encrypt_info_dict(info, config, use_platform_host, dump_dict=True)
        logging.debug("Try Send")
        logging.debug(mes)
        res = send_request(mes, url_special, csrf, proxy=proxy, username=username,
                           password=password, timeout=timeout, ignore_certificate=ignore_certificate)
        logging.info(res)
        return res
    except Exception:
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #
        # print(traceback.format_exc())
        # print_info_log(' '.join(["EXCEPTION", str(exc_type), fname, str(exc_tb.tb_lineno)]))
        logging.critical("EXCEPTION", exc_info=True)


