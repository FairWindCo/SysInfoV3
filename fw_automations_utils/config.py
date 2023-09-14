from __future__ import annotations

import json
import logging
import os
import sys


def get_config(config_file='config.json', exit_on_error=True, default_config=None):
    config = default_config if default_config else {}
    try:
        if os.path.exists(config_file):
            json_data = open(config_file).read()
            config.update(json.loads(json_data))
        else:
            if exit_on_error:
                logging.critical(f'ERROR: config {config_file} - not exists!')
                sys.exit(-1)
    except Exception as e:
        if exit_on_error:
            logging.critical('ERROR ' + str(e), exc_info=True)
            sys.exit(-1)
        else:
            logging.warning('WARNING ' + str(e), exc_info=True)
    return config


def set_config(config, config_file='config.json'):
    try:
        config_text = json.dumps(config)
        open(config_file, 'wt').write(config_text)
    except Exception as e:
        logging.error('WARNING ' + str(e), exc_info=True)
