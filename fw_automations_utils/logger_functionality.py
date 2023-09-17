import logging
import sys
from io import StringIO

from fw_automations_utils.config import get_config

IS_ERROR_LOGGED = False


def fatal(msg, *args, **kwargs):
    global IS_ERROR_LOGGED
    IS_ERROR_LOGGED = True
    logging.fatal(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    global IS_ERROR_LOGGED
    IS_ERROR_LOGGED = True
    logging.error(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    global IS_ERROR_LOGGED
    IS_ERROR_LOGGED = True
    logging.exception(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    global IS_ERROR_LOGGED
    IS_ERROR_LOGGED = True
    logging.critical(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    logging.warning(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    logging.info(msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    logging.debug(msg, *args, **kwargs)


def setup_default_logger_from_config(config: dict):
    log_file = config.get('log_file', 'operation.log')
    new_file_log = config.get('new_file_log', True)
    if log_file:
        if new_file_log:
            logging.basicConfig(filename=log_file, encoding='utf-8',
                                level=get_debug_level_from_config(config), filemode='w')
        else:
            logging.basicConfig(filename=log_file, encoding='utf-8',
                                level=get_debug_level_from_config(config))
    else:
        logger = logging.getLogger()
        logger.setLevel(get_debug_level_from_config(config))
    logging.debug(f"CURRENT CONFIG: {config}")
    return log_file


def get_config_and_set_logger(config_file='config.json', exit_on_error=True, default_config=None):
    backup_config = get_config(config_file, default_config=default_config, exit_on_error=exit_on_error)
    log_file = setup_default_logger_from_config(backup_config)
    return backup_config, log_file


def get_debug_level_from_config(config: dict, default_debug_level=logging.WARNING):
    str_debug_level = config.get('log_level', None)
    if str_debug_level:
        return get_debug_level(str_debug_level)
    else:
        return default_debug_level


def get_debug_level(level_name: str):
    name = level_name.upper()
    if name == 'INFO':
        return logging.INFO
    if name == 'WARNING' or name == 'WARN':
        return logging.WARNING
    if name == 'ERROR' or name == 'ERR':
        return logging.ERROR
    if name == 'CRITICAL' or name == 'CRIT':
        return logging.CRITICAL
    if name == 'DEBUG':
        return logging.DEBUG
    if name == 'FATAL':
        return logging.FATAL
    if name == 'NO' or name == 'NOTSET' or name == '-':
        return logging.NOTSET
    return logging.NOTSET


def setup_logger(config: dict, name=None):
    if config is None:
        config = {}
    if name and name in config:
        config = config.get(name)
    logger = logging.getLogger(name)
    debug = get_debug_level(config.get('log_level', 'warn'))
    logger.setLevel(debug)
    if config.get('log_console', True):
        logger.addHandler(logging.StreamHandler(sys.stdout))
    file_name = config.get('log_file', None)
    if file_name:
        logger.addHandler(logging.FileHandler(file_name))
    formater = config.get('formatter', None)
    if formater:
        logger.setFormatter(logging.Formatter(formater))
    if config.get('buffer_logging', False):
        if config.get('buffer_to_log', None):
            buffer = config.get('buffer_to_log')
        else:
            buffer = StringIO(newline='\n')
            config['buffer_to_log'] = buffer
        logger.addHandler(logging.StreamHandler(buffer))
    return logger
