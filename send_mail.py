import argparse
import logging
import os.path
from pprint import pprint

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading
from fw_automations_utils.logger_functionality import setup_logger
from fw_automations_utils.config import get_config
from fw_server_communications.mail_reports import send_mail_ex

if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser()
    parser.add_argument('--error', dest='is_error', action='store_true')
    parser.add_argument('-c', dest='config', default='mail.json')
    parser.add_argument('-m', dest='message', default='test message')
    parser.add_argument('-s', dest='server', action="store")
    parser.add_argument('-f', dest='from_mail', default="Department_BSP@erc.ua")
    parser.add_argument('-t', dest='to_mail')
    parser.add_argument('-p', dest='port')

    arguments = parser.parse_args()
    if os.path.exists(arguments.config):
        config = get_config(arguments.config)
    else:
        config = {
            'server': '127.0.0.1',
            'port': 25,
            'from_mail': "Department_BSP@erc.ua",
            'to_mail': "Department_BSP@erc.ua",
            'mail_type': "HTML",
        }
    if arguments.server is not None and arguments.server:
        config['server'] = arguments.server
    if arguments.from_mail is not None and arguments.from_mail:
        config['from_mail'] = arguments.from_mail
    if arguments.to_mail is not None and arguments.to_mail:
        config['to_mail'] = arguments.to_mail
    if arguments.port is not None and arguments.port:
        config['port'] = arguments.port
    setup_logger(config)
    result = send_mail_ex(arguments.message, config, arguments.is_error)
    if result['success']:
        logging.info(f'SEND MAIL start at {result["smtp_session_start_time"]}')
        logging.info(f'MAIL SEND - SUCCESS to server: {result["mail_send_to_server"]}')
        logging.info(
            f'smtp session time={result["smtp_session_time"] / 10 ** 9}s '
            f'sending time is {result["mail_send_time"] / 10 ** 9}s')
    else:
        pprint(result)
    th.join()
