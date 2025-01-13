# pyinstaller --noconfirm --onefile --console --collect-submodules=sspilib --add-data "C:/Program Files/MIT/Kerberos/bin;bin/"  "D:/USER_DATA/Serhii/PycharmProjects/SysInfoV3/send_message.py"

import argparse
import logging
import os.path
import sys

from fw_automations_utils.clear_temp_folder import cleanup_mei_threading
from fw_automations_utils.config import get_config
from fw_automations_utils.logger_functionality import setup_logger
from fw_server_communications.inventory_communications import report_to_server
from fw_server_communications.mail_reports import send_mail_ex
from fw_utils.simple_telegram import send_notify

if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser()
    parser.add_argument('--error', dest='is_error', action='store_true')
    parser.add_argument('-m', dest='message', default='')
    parser.add_argument('-k', dest='control_code', default=31)

    parser.add_argument('-c', dest='config', default='message.json')
    parser.add_argument('-d', dest='dont_mail_on_error', action="store_true")

    parser.add_argument('-u', dest='report_url', action="store")
    parser.add_argument('-g', dest='token_url', action="store")
    parser.add_argument('-r', dest='proxy', action="store")
    parser.add_argument('-s', dest='server', action="store")
    parser.add_argument('--host', dest='host', action="store")
    parser.add_argument('-f', dest='from_mail', default="Department_BSP@erc.ua")
    parser.add_argument('-t', dest='to_mail', default="Department_BSP@erc.ua")
    parser.add_argument('-pl', '--proxy_list', action='append')
    parser.add_argument('-p', dest='port')
    parser.add_argument('--mail', dest='send_mail', action="store_true")
    parser.add_argument('--telegram', dest='send_telegram', action="store_true")
    parser.add_argument('--dont_report', dest='dont_report', action="store_true")
    parser.add_argument('--token', dest='telegram_token')
    parser.add_argument('--chart', dest='telegram_chat')

    arguments = parser.parse_args()
    config = {
        'server': 'web01.local.erc',
        'port': 25,
        'from_mail': "Department_BSP@erc.ua",
        'to_mail': "Department_BSP@erc.ua",
        'mail_type': "HTML",
        "token_url": r"https://inventory0201.bs.local.erc/token",
        "special_url": r"https://inventory0201.bs.local.erc/special",
#        "token_url": r"http://127.0.0.1/token",
#        "special_url": r"http://127.0.0.1/special",

        "selected_proxy": r"http://fw02.bs.local.erc:8080/",
        'round_robin_proxy': [r"http://fw02.bs.local.erc:8080/", r"http://fw01.bs.local.erc:8080/", None],
        'send_report_code': 31,
        "telegram_chat_id": -1001860555177,
    }
    if os.path.exists(arguments.config):
        config.update(get_config(arguments.config))


    if arguments.server is not None and arguments.server:
        config['server'] = arguments.server
    if arguments.host is not None and arguments.host:
        config['host'] = arguments.host
    if arguments.from_mail is not None and arguments.from_mail:
        config['from_mail'] = arguments.from_mail
    if arguments.to_mail is not None and arguments.to_mail:
        config['to_mail'] = arguments.to_mail
    if arguments.port is not None and arguments.port:
        config['port'] = arguments.port
    if arguments.token_url is not None and arguments.token_url:
        config['token_url'] = arguments.port
    if arguments.report_url is not None and arguments.report_url:
        config['special_url'] = arguments.port
    if arguments.proxy is not None and arguments.proxy:
        logging.debug("set selected proxy to: %s", arguments.proxy)
        config['selected_proxy'] = arguments.proxy
    if arguments.control_code is not None and arguments.control_code:
        config['send_report_code'] = arguments.control_code
    if arguments.proxy_list is not None and arguments.proxy_list:
        logging.debug("set round robin proxy to: %s", arguments.proxy_list)
        config['round_robin_proxy'] = arguments.proxy_list
    if arguments.telegram_token is not None and arguments.telegram_token:
        config['telegram_token'] = arguments.telegram_token
    if arguments.telegram_chat is not None and arguments.telegram_chat:
        config['telegram_chat_id'] = arguments.telegram_chat

    setup_logger(config)
    logging.info("SENDING MESSAGE")
    logging.debug(config)
    try:
        if not arguments.dont_report:
            report_to_server(arguments.message, config=config, state_error=arguments.is_error)
    except Exception as e:
        if not arguments.dont_mail_on_error:
            send_mail_ex(f"Error in message send: {e}", config, True)
        sys.exit(-1)
    if arguments.send_mail:
        result = send_mail_ex(arguments.message, config, arguments.is_error)
        if result['success']:
            logging.info(f'MAIL SEND - SUCCESS to server: {result["mail_send_to_server"]}')
    if arguments.send_telegram:
        result = send_notify(config, arguments.message)
        logging.info(f'TELEGRAM SEND: {result}')
    th.join()
    sys.exit(0)
