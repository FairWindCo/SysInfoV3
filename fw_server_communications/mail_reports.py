from __future__ import annotations

import logging
import platform
import smtplib
import sys
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from os.path import basename


def send_mail(message, config):
    SMTP_SERVER = config.get('server', '127.0.0.1')
    SMTP_PORT = config.get('port', 25)
    FROM_MAIL = config.get('from_mail', '').strip().lower()
    USER_MAIL = config.get('mail_user', '')
    PASS_MAIL = config.get('mail_pass', '')
    TO_MAIL = config.get('to_mail', "BSPD_reports@erc.ua").strip().lower()
    try:
        start_smtp_session = time.monotonic_ns()
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if USER_MAIL:
            smtp.login(USER_MAIL, PASS_MAIL)
        start_mail_send = time.monotonic_ns()
        smtp.sendmail(FROM_MAIL, TO_MAIL, message)
        end_time = time.monotonic_ns()
        return {
            'smtp_session_start_time': datetime.now(),
            'smtp_session_time': end_time - start_smtp_session,
            'mail_send_time': end_time - start_mail_send,
            'mail_send_to_server': f'{SMTP_SERVER}:{SMTP_PORT}',
            'success': True,
        }
    except Exception as e:
        logging.debug(f'{SMTP_SERVER}:{SMTP_PORT} - WARNING: {str(e)} [{type(e).__name__}]', exc_info=True)
        return {
            'error': str(e),
            'error_type': type(e).__name__,
            'mail_send_to_server': f'{SMTP_SERVER}:{SMTP_PORT}',
            'success': True,
        }


def format_message(message_text: str, config: dict, error: bool = False, files=None):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    host = platform.node()
    script = sys.argv[0]
    part1 = MIMEText(message_text, "plain")
    message = MIMEMultipart("alternative")
    if error:
        message["Subject"] = "ERROR: on server {} in script {} ".format(host, script)
        html = """\
        <html>
          <body>
            <p>
                <b style="color:red">ON SERVER {} IN SCRIPT {} GOT ERROR:</b>
            </p>
            <p>
            {}
            </p>
          </body>
        </html>
        """.format(host, script, message_text)
    else:
        message["Subject"] = "INFO: from {} script {} ".format(host, script)
        html = """\
                <html>
                  <body>
                    <p>
                        <b style="color:green">SERVER {} IN SCRIPT {} INFO:</b>
                    </p>
                    <p>
                    {}
                    </p>
                  </body>
                </html>
                """.format(host, script, message_text)

    message["From"] = config.get('from_mail', '')
    message["To"] = config.get('to_mail', "bspd@erc.ua")

    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)
    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        message.attach(part)
    return message


def send_mail_mime(message, config, is_error=False, files=None):
    msg = format_message(message, config, is_error, files=files)
    return send_mail(msg.as_string(), config)


def send_mail_ex(message, config, is_error=False):
    logging.info('TRY SEND MAIL')
    SMTP_MAIL_TYPE = config.get('mail_type', 'HTML')
    if SMTP_MAIL_TYPE.upper() == 'HTML':
        logging.info("Send email in MIME format")
        return send_mail_mime(message, config, is_error)
    else:
        logging.info("Send email in TEXT format")
        if is_error:
            logging.error("SEND ERROR MESSAGE MAIL")
            return send_mail('ERROR ON SERVER: {} SCRIPT: {} MESSAGE: {}'.format(platform.node(), sys.argv[0], message),
                             config)
        else:
            logging.info("SEND SUCCESS MESSAGE MAIL")
            return send_mail('SERVER: {} SCRIPT: {} MESSAGE: {}'.format(platform.node(), sys.argv[0], message), config)
