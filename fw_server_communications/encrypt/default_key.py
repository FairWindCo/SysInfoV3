import logging
import sys

from rsa import PublicKey

DEFAULT_KEY = b'''-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBALkEJ45fChQnrvrkn7EIrVIHQGyVSUwAMOkGy0oBke/8ucnylzQ3ORPH
PVd8opS5dj6SRqvqcjY+rpuScxC32U/Et95ykYQjhMJAbDiAVLRneJueYchlu5Gb
krYuV3bb6Ano8ut/sQI0IT047PVsp2njeCOSN0HbhBCqLNK5lVGBAgMBAAE=
-----END RSA PUBLIC KEY-----'''


def load_key_default():
    try:
        return PublicKey.load_pkcs1(DEFAULT_KEY)
    except Exception as e:
        logging.debug('ERROR ' + str(e))
        sys.exit(-2)
