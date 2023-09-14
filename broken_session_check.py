import json
import re
import subprocess

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading

session_column_reg = re.compile(
    r'(?P<session>\S+|\s)\s{2,17}'
    r'(?P<username>\S+|\s)\s{2,25}'
    r'(?P<session_id>\S+)\s{2,6}'
    r'(?P<state>\S+)\s{2,6}'
    r'(?P<type>\S*)\s{2,}'
    r'(?P<device>\S*)\s*'
)


def parse_session_columns(result_line: str) -> dict:
    line_for_parse = result_line[1:] if result_line[0] == ' ' else result_line
    line_for_parse += '      '
    result = session_column_reg.match(line_for_parse)
    if result:
        ses = result.groupdict()
        ses['session'] = None if ses['session'] == ' ' else ses['session'].strip()
        ses['username'] = None if ses['username'] == ' ' else ses['username'].strip()
        ses['is_broken'] = ses['username'] is None and ses['session'] is None
        ses['session_id'] = int(ses['session_id'].strip())
        ses['is_special'] = ses['session'] == 'services' or ses['session'] == 'console' or ses['session_id'] > 65535
        return ses
    else:
        raise ValueError(f'incorrect line:[{result_line}]')


def _test_work():
    template_data = """
 SESSIONNAME       USERNAME                 ID  STATE   TYPE        DEVICE
 services                                    0  Disc
 console                                     1  Conn
>rdp-tcp#0         msy                       2  Active
                   msy                      22  Disc
                                            23  Disc                   
 31c5ce94259d4...                        65536  Listen
 rdp-tcp                                 65537  Listen
"""

    for line in template_data.split("\n")[2:]:
        if line:
            print(parse_session_columns(line))


def list_sessions() -> list:
    p = subprocess.run(['query', 'session'], shell=True, timeout=20, capture_output=True)
    if p.returncode == 1:
        return [parse_session_columns(line) for line in p.stdout.decode().split('\r\n')[1:] if line]
    else:
        return ()


def control_sessions():
    session_list = list_sessions()
    total_sessions = len(session_list)
    active = 0
    broken = 0
    special = 0
    disc = 0
    other = 0
    active_users = []
    disc_users = []
    for ses in session_list:
        if ses['is_broken']:
            broken += 1
            continue
        if ses['is_special']:
            special += 1
            continue
        if ses['state'] == 'Active':
            active += 1
            if ses['username']:
                active_users.append(ses['username'])
        elif ses['state'] == 'Disc':
            disc += 1
            if ses['username']:
                disc_users.append(ses['username'])
        else:
            other += 1
    return {
        'total_sessions': total_sessions,
        'active_sessions': active,
        'disconnect_sessions': disc,
        'broken_sessions': broken,
        'special_sessions': special,
        'other_sessions': other,
        'active': ','.join(active_users),
        'disconect': ','.join(disc_users),
        'sessions': session_list
    }


if __name__ == "__main__":
    th = cleanup_mei_threading()
    print(json.dumps(control_sessions()))
    # cleanup_mei(debug=True)
    th.join()
# print(re.split(' +', line))
