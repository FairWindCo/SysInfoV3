import logging
import sys
from io import StringIO

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
