import argparse
import logging
import os.path
import sys

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading
from fw_automations_utils.config import get_config
from fw_automations_utils.logger_functionality import setup_logger
from fw_server_communications.inventory_communications import report_to_server
from fw_server_communications.mail_reports import send_mail_ex

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
    parser.add_argument('-f', dest='from_mail', default="Department_BSP@erc.ua")
    parser.add_argument('-t', dest='to_mail', default="Department_BSP@erc.ua")
    parser.add_argument('-pl', '--proxy_list', action='append')
    parser.add_argument('-p', dest='port')

    arguments = parser.parse_args()
    if os.path.exists(arguments.config):
        config = get_config(arguments.config)
    else:
        config = {
            'server': 'web01.bs.local.erc',
            'port': 25,
            'from_mail': "Department_BSP@erc.ua",
            'to_mail': "Department_BSP@erc.ua",
            'mail_type': "HTML",
            "token_url": r"https://inventory0201.bs.local.erc/token",
            "special_url": r"https://inventory0201.bs.local.erc/special",
            "proxy": r"http://fw01.bs.local.erc:8080/",
            'round_robin_proxy': [r"http://fw02.bs.local.erc:8080/", r"http://fw01.bs.local.erc:8080/", None],
            'send_report_code': 31,
        }
    if arguments.server is not None and arguments.server:
        config['server'] = arguments.server
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
        config['proxy'] = arguments.proxy
    if arguments.control_code is not None and arguments.control_code:
        config['send_report_code'] = arguments.control_code
    if arguments.proxy_list is not None and arguments.proxy_list:
        config['round_robin_proxy'] = arguments.proxy_list

    setup_logger(config)
    logging.info("SENDING MESSAGE")
    logging.debug(config)
    try:
        report_to_server(arguments.message, config=config, state_error=arguments.is_error)
    except Exception as e:
        send_mail_ex(f"Error in message send: {e}", config, True)
        sys.exit(-1)
    if arguments.is_error and not arguments.dont_mail_on_error:
        result = send_mail_ex(arguments.message, config, arguments.is_error)
        if result['success']:
            logging.info(f'MAIL SEND - SUCCESS to server: {result["mail_send_to_server"]}')
    th.join()
    sys.exit(0)
