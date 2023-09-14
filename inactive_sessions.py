import argparse
import json
import logging
import os
import sys

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading
from fw_automations_utils.logger_functionality import setup_logger
from fw_server_communications.inventory_communications import report_to_server
from fw_automations_utils.config import get_config
from fw_automations_utils.winsys_utils import list_logged_users, list_RDP_logged_users, list_all_process_users


def analise_process_info(user_id, process_struct, rdp_sessions: dict, user_logged: dict, add_proc_info=False) -> dict:
    rdp_info = rdp_sessions.get(user_id, None)
    user_info = user_logged.get(user_id, None)
    info = {
        'has_user': True if user_info else False,
        'has_process': True if process_struct else False,
        'has_rdp': True if rdp_info else False
    }

    if process_struct:
        info['count_process'] = process_struct['count_process']
        info['use_mem'] = process_struct['use_mem']
        if add_proc_info:
            info['process_list'] = process_struct['proc_list']
    else:
        info['count_process'] = 0
        info['use_mem'] = 0

    if user_info:
        info['username'] = user_info['username']
        info['session'] = user_info['session_name']
        info['logon_time'] = user_info['logon_time']
        info['state'] = user_info['state']
        info['has_user'] = True
    if rdp_info:
        info['has_rdp'] = True
        info['username'] = rdp_info['username']
        if 'session' not in info:
            info['session'] = rdp_info['session_name']
        if 'state' not in info:
            info['state'] = rdp_info['state']
    return info


def form_total_sessions_info() -> dict:
    rdp_sessions = convert_session_list_to_dict(list_RDP_logged_users())
    users = convert_session_list_to_dict(list_logged_users())
    user_process = group_list_process_by_session(list_all_process_users())
    logging.debug(rdp_sessions)
    logging.debug(users)

    response = {user_id: analise_process_info(user_id, process_list, rdp_sessions, users)
                for user_id, process_list in user_process.items()}
    for rdp_session_id in rdp_sessions.keys():
        if rdp_session_id not in response:
            response[rdp_session_id] = analise_process_info(rdp_session_id, None, rdp_sessions, users)
    for session_id in users.keys():
        if session_id not in response and session_id not in rdp_sessions:
            response[session_id] = analise_process_info(session_id, None, rdp_sessions, users)
    return response


def convert_session_list_to_dict(list_sessions: list) -> dict:
    return {session['id']: session for session in list_sessions}


def group_list_process_by_session(list_process: list) -> dict:
    sessions_process = {}
    for process_info in list_process:
        session_id = process_info['session_num']
        strct = sessions_process.setdefault(session_id, {'count_process': 0, 'use_mem': 0, 'proc_list': []})
        strct['proc_list'].append(process_info)
        strct['count_process'] = strct['count_process'] + 1
        strct['use_mem'] = strct['use_mem'] + process_info['mem']
    return sessions_process


def analyse_sessions(total_sessions: dict) -> tuple[bool, int]:
    has_inactive_session = False
    inactive_count = 0
    for session_id, session in total_sessions.items():
        if (session['username'] == '---' or not session['username']) and session['session'] != 'services':
            has_inactive_session = True
            session['is_inactive'] = True
            inactive_count += 1
        elif not session['has_process']:
            has_inactive_session = True
            session['is_inactive'] = True
            inactive_count += 1
        elif not session['has_user'] and session['session'] != 'services':
            has_inactive_session = True
            session['is_inactive'] = True
            inactive_count += 1
        else:
            session['is_inactive'] = False
    return has_inactive_session, inactive_count


if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', dest='control_code', default=19)
    parser.add_argument('-c', dest='config', default='inactive_config.json')
    parser.add_argument('-u', dest='report_url', action="store")
    parser.add_argument('-g', dest='token_url', action="store")
    parser.add_argument('-r', dest='proxy', action="store")
    parser.add_argument('-f', dest='report_file', default='inactive.json')
    parser.add_argument('-dw', dest='not_write_report', action="store_false")

    arguments = parser.parse_args()
    if os.path.exists(arguments.config):
        config = get_config(arguments.config)
    else:
        config = {
            "token_url": r"https://inventory0201.bs.local.erc/token",
            "special_url": r"https://inventory0201.bs.local.erc/special",
            "proxy": r"http://fw01.bs.local.erc:8080/",
            'send_report_code': 19,
        }
    if arguments.token_url is not None and arguments.token_url:
        config['token_url'] = arguments.port
    if arguments.report_url is not None and arguments.report_url:
        config['special_url'] = arguments.port
    if arguments.proxy is not None and arguments.proxy:
        config['proxy'] = arguments.proxy
    if arguments.control_code is not None and arguments.control_code:
        config['send_report_code'] = arguments.control_code

    setup_logger(config)
    total_sessions = form_total_sessions_info()
    is_inactive, count = analyse_sessions(total_sessions)
    total_sessions['total_sessions_count'] = len(total_sessions)
    total_sessions['is_inactive'] = is_inactive
    total_sessions['inactive_sessions_count'] = count
    logging.info(f"Has inactive sessions: {is_inactive}")
    if is_inactive:
        logging.info(f"Inactive sessions count: {count}")
    if arguments.report_file and arguments.not_write_report:
        try:
            with open(arguments.report_file, "wt") as f:
                json.dump(total_sessions, f)
        except Exception as _:
            logging.exception("Report Form Error")
    try:
        report_to_server(f"Broken session check: {is_inactive}", config=config, state_error=False)
    except Exception as e:
        logging.exception("Send message Error")
        sys.exit(-1)
    th.join()
    sys.exit(0)

