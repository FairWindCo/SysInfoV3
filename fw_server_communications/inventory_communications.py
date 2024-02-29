from __future__ import annotations

import logging
import platform

from fw_server_communications.encrypt.message_sign import encrypt_info_dict, extract_host_name
from fw_server_communications.mail_reports import send_mail_ex
from fw_server_communications.server_requests import ServerRequestor, ResponseStateRequest


def send_info(info, config=None, use_platform_host=True,
              url_default='http://127.0.0.1:8000/host_info_update'):
    result = send_info_request(info, config, use_platform_host, url_default)
    if result is not None and result['status'] != ResponseStateRequest.OK:
        logging.debug('Communication Error while request')
        return False
    else:
        json_response = result['response'].json()
        if json_response['result'] == "ok":
            logging.info("REQUEST SUCCESS")
            return True
        else:
            logging.debug('RESONSE WITH ERROR:' + json_response['message'])
            return False


def send_info_request(info, config=None, use_platform_host=True,
                      url_default='http://127.0.0.1:8000/host_info_update'):
    try:
        if config is None:
            config = {}
        url_special = config.get('special_url', url_default)
        requestor = ServerRequestor(config)
        mes = encrypt_info_dict(info, config, use_platform_host, dump_dict=True)
        logging.debug(f'SEND DATA: {mes}')
        res = requestor.request_with_csrf(url_special, mes)
        logging.info(res)
        return res
    except Exception:
        logging.critical("EXCEPTION", exc_info=True)
        return {
            'response': None,
            'status': ResponseStateRequest.COMMUNICATION_ERROR
        }


def send_report_error(message: str, config: dict):
    logging.info("ERROR REPORT: ", message)
    SEND_REPORT_MAIL = config.get('send_report_mail', True)
    SEND_REPORT_WEB = config.get('send_report_web', True)
    logging.debug(message)
    if SEND_REPORT_MAIL:
        send_mail_ex(str(message), config, is_error=True)
    if SEND_REPORT_WEB:
        report_to_server(str(message), config, True)


def report_to_server(message, config, state_error=False, ):
    logging.info('TRU SEND REPORT TO SERVER')
    SEND_REPORT_WEB = config.get('send_report_web', True)
    TASK_CODE = config.get('send_report_code', None)
    if SEND_REPORT_WEB:
        from time import ctime
        mes = {
            'message': message,
            'time': ctime(),
            'is_error': state_error,
            'host': extract_host_name(config),
        }
        if TASK_CODE:
            mes['task_code'] = TASK_CODE
        try:
            logging.info(message)
            return send_info_request(mes, config, use_platform_host=True,
                                     url_default='http://127.0.0.1:8000/special')
        except Exception:
            logging.critical("EXCEPTION", exc_info=True)
            return {
                'response': None,
                'status': ResponseStateRequest.COMMUNICATION_ERROR
            }
