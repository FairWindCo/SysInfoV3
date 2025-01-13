import logging

import requests


def update_telegram(config):
    logging.debug(config)
    telegram_token = config.get('telegram_token', None)
    proxy_url = config.get('telegram_proxy_url', '')

    proxy = {'https': proxy_url,
             'http': proxy_url,
             } if proxy_url else {}

    url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
    if not telegram_token:
        return None
    logging.debug(f"URL: {url} PARAMS: {proxy}")
    res = requests.get(url, proxies=proxy).json()
    logging.debug(res)
    return res


def send_telegram_message(config, message):
    logging.debug(config)
    telegram_token = config.get('telegram_token')
    telegram_chat_id = config.get('telegram_chat_id')
    proxy_url = config.get('telegram_proxy_url', '')

    proxy = {'https': proxy_url,
             'http': proxy_url,
             } if proxy_url else {}

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={telegram_chat_id}&text={message}"
    logging.debug(f"URL: {url} PARAMS: {proxy}")
    res = requests.get(url, proxies=proxy).json()  # this sends the message
    logging.debug(res)
    return res


def send_notify(config, message):
    selected_proxy = config.get('selected_proxy', None)
    round_robin_proxy = config.get('round_robin_proxy', None)
    auto_select_proxy = config.get('auto_select_proxy', True)
    if not auto_select_proxy or (round_robin_proxy is None or selected_proxy):
        logging.debug("Use selected proxy for")
        proxy_list = [selected_proxy]
    else:
        logging.debug("Auto select proxy")
        proxy_list = round_robin_proxy
    for proxy in proxy_list:
        config['telegram_proxy_url'] = proxy
        try:
            if update_telegram(config):
                return send_telegram_message(config, message)
            else:
                logging.error("no response from telegram")
        except Exception as e:
            logging.error(f"Exception on send telegram: {e}")
    return None