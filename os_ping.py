import argparse
import json
import re
import subprocess
import sys

from fw_automations_utils.clear_temp_folder import cleanup_mei, cleanup_mei_threading


class SystemPing:
    def __init__(self, host: str, count: int = 4, packet_size: int = 56, interval: int = 1000) -> None:
        super().__init__()
        self.host = host
        self.count = count or 4
        self.packet_size = packet_size or 56
        self.interval = interval or 1
        self._std_out = None
        self.result = None
        self.ping_command = 'ping'
        self.in_shell = False
        self.split_symbol = '\r'

    def analise_std_out(self) -> dict:
        return {}

    def run(self):
        result = subprocess.run(self.ping_command, stdout=subprocess.PIPE, shell=self.in_shell)
        if result.returncode == 0 or result.returncode == 1:
            self._std_out = list(
                map(str.strip, filter(lambda s: s.strip(), result.stdout.decode().split(self.split_symbol))))
            self.result = self.analise_std_out()
        self.result['is_error'] = result.returncode != 0
        return self.result


class SystemWinPing(SystemPing):
    def __init__(self, host: str, count: int = 4, packet_size: int = 56, interval: int = 1000) -> None:
        super().__init__(host, count, packet_size, interval)
        self.ping_command = f'ping {host} -n {count} -l {packet_size} -w {interval}'
        self.regexp_parent = re.compile(r"^Ping statistics for (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):")
        self.regexp_lost = re.compile(r"^Packets: Sent = (\d+), Received = (\d+), Lost = (\d+) \((\d+)% loss\),")
        self.regexp_time = re.compile(r"^Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms")
        self.one_resp = re.compile(r".* time=(\d+)ms .*")
        self.dest_unrich = re.compile(r".*(Destination host unreachable.|Request timed out.)")

    def analise_std_out(self) -> {}:
        length = len(self._std_out)
        index = 0
        jitter = 0
        delay = 0
        unrich = 0
        last_delay = None
        min_jit = None
        max_jit = 0
        avg_jit = 0
        count_jit = 0
        result = {
            'peer': self.host,
            'lost': 0,
            'avg_rtt': 0,
            'jitter': 0,
        }
        while index < length:
            # print(self._std_out[index])
            match_line = self.one_resp.match(self._std_out[index])
            if match_line:
                delay = float(match_line.group(1))
                if last_delay is None:
                    last_delay = delay
                else:
                    count_jit += 1
                    jitter = abs(last_delay - delay)
                    last_delay = delay
                    avg_jit += jitter
                    min_jit = jitter if min_jit is None or min_jit > jitter else min_jit
                    max_jit = jitter if max_jit < jitter else max_jit
            else:
                match_unrich = self.dest_unrich.match(self._std_out[index])
                if match_unrich:
                    unrich += 1
            match_peer = self.regexp_parent.match(self._std_out[index])
            if match_peer:
                result['parent'] = match_peer.group(1)
                index += 1
                match_loss = self.regexp_lost.match(self._std_out[index])
                if match_loss:
                    result['packet_lost'] = int(match_loss.group(3))
                    result['loss'] = float(match_loss.group(4))
                    result['send'] = int(match_loss.group(1))
                    result['recv'] = int(match_loss.group(2))
                    result['avg_jitter'] = avg_jit / count_jit if count_jit > 0 else 0
                    result['max_jitter'] = max_jit
                    result['min_jitter'] = min_jit
                    index += 1
                    if unrich == self.count:
                        result['lost'] = unrich
                        result['loss'] = 100
                        result['recv'] = 0
                        result['packet_lost'] = unrich
                        result['min_rtt'] = self.interval
                        result['max_rtt'] = self.interval
                        result['avg_rtt'] = self.interval
                        result['min_jitter'] = 0
                    elif result['loss'] < 100 and len(self._std_out) > index:
                        index += 1
                        match_timing = self.regexp_time.match(self._std_out[index])
                        if match_timing:
                            result['min_rtt'] = float(match_timing.group(1))
                            result['max_rtt'] = float(match_timing.group(2))
                            result['avg_rtt'] = float(match_timing.group(3))
                            break
                    else:
                        break
            index += 1
        return result


class SystemLinuxPing(SystemPing):
    def __init__(self, host: str, count: int = 4, packet_size: int = 56, interval: int = 1) -> None:
        super().__init__(host, count, packet_size, interval)
        self.ping_command = f'ping {host} -c {count} -i {interval} -s {packet_size}'
        self.regexp_parent = re.compile(r"^--- (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) ping statistics ---")
        self.regexp_lost = re.compile(
            r"^(\d+) packets transmitted, (\d+) received, ([+-]?\d*\.?\d*)% packet loss, time (\d+)ms")
        self.regexp_time = re.compile(
            r"^rtt min/avg/max/mdev = ([+-]?\d*\.?\d*)/([+-]?\d*\.?\d*)/([+-]?\d*\.?\d*)/([+-]?\d*\.?\d*) ms")
        self.in_shell = True
        self.split_symbol = '\n'

    def analise_std_out(self) -> dict:
        length = len(self._std_out)
        index = 0
        result = {
            'peer': self.host,
            'packet_lost': 0,
        }
        while index < length:
            match_peer = self.regexp_parent.match(self._std_out[index])
            if match_peer:
                result['parent'] = match_peer.group(1)
                index += 1
                match_loss = self.regexp_lost.match(self._std_out[index])
                if match_loss:
                    result['loss'] = float(match_loss.group(3))
                    result['send'] = int(match_loss.group(1))
                    result['recv'] = int(match_loss.group(2))
                    result['timing'] = int(match_loss.group(4))
                    index += 1
                    if result['loss'] < 100:
                        match_timing = self.regexp_time.match(self._std_out[index])
                        if match_timing:
                            result['min_rtt'] = float(match_timing.group(1))
                            result['max_rtt'] = float(match_timing.group(3))
                            result['avg_rtt'] = float(match_timing.group(2))
                            result['mdev'] = float(match_timing.group(4))
                            break
                    else:
                        break
            index += 1
        return result


def create_ping_service(host: str, count: int = 4, packet_size: int = 56, interval: int = 1000):
    if sys.platform == 'win32':
        return SystemWinPing(host, count, packet_size, interval)
    else:
        return SystemLinuxPing(host, count, packet_size, int(interval / 1000))


if __name__ == "__main__":
    th = cleanup_mei_threading()
    parser = argparse.ArgumentParser(description='this is utility to transform system ping to json')
    parser.add_argument('server', nargs=1, type=str, action='store')
    parser.add_argument('count', nargs='?', type=int, action='store', default=4)
    parser.add_argument('timeout', nargs='?', type=int, action='store', default=1000)
    arguments = parser.parse_args()
    # pinger = create_ping_service('8.8.8.8')
    pinger = create_ping_service(arguments.server[0], count=arguments.count, interval=arguments.timeout)
    print(json.dumps(pinger.run()))
    th.join()
