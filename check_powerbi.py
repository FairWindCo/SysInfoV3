import datetime
import json

import urllib3
from tabulate import tabulate

from fw_utils.utils import sizeof_fmt

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from requests_ntlm import HttpNtlmAuth


def get_report(user, password, proxy=None):
    basic = HttpNtlmAuth(user, password)
    start_time = datetime.datetime.now()
    try:
        response = requests.get(
            'https://pbirs0001.local.erc/reports/api/v2.0/catalogitems(4631e52a-3dd3-459d-9e4e-c678da752b1e)/Content/$value',
            auth=basic, verify=False,
            proxies=proxy)
        code = response.status_code
        size = len(response.content)
        with open("report_file", "wb") as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(e)
        code = -1
        size = 0
    # print(response.content)
    timing = datetime.datetime.now() - start_time
    return code, timing, size


def test(user, password, number, proxy=None):
    data = []
    for i in range(number):
        code, timing, size = get_report(user, password)
        data.append((i + 1, code, timing, sizeof_fmt(size)))
    print(tabulate(data, headers=["#", "Reponse Code", "Time", "Size"]))


def test_config(file_name="auth.json"):
    with open(file_name, "rt") as f:
        auth = json.load(f)
        test(auth["user"], auth["password"], auth.get('numbers', 5), auth.get("proxy", None))


if __name__ == "__main__":
    test_config()
