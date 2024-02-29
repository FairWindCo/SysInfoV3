#!/usr/bin/env python
# pyinstaller --noconfirm --onefile --console  "C:\Users\User\PycharmProjects\SysInfoV3\fw_utils\disk_test.py"
from __future__ import division, print_function  # for compatability with py2

import argparse
import json
import os
import platform
import random
import sys
import tempfile
from random import shuffle
from threading import Thread

import wmi

from fw_utils.utils import sizefmt

try:  # if Python >= 3.3 use new high-res counter
    from time import perf_counter as time, sleep
except ImportError:  # else select highest available resolution counter
    if sys.platform[:3] == 'win':
        from time import clock as time
    else:
        from time import time


def get_args():
    parser = argparse.ArgumentParser(description='Arguments', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--file',
                        required=False,
                        action='store',
                        default=os.path.join(tempfile.gettempdir(), 'monkeytest'),
                        help='The file to read/write to')
    parser.add_argument('-s', '--size',
                        required=False,
                        action='store',
                        type=int,
                        default=128,
                        help='Total MB to write')
    parser.add_argument('-w', '--write-block-size',
                        required=False,
                        action='store',
                        type=int,
                        default=1024,
                        help='The block size for writing in bytes')
    parser.add_argument('-r', '--read-block-size',
                        required=False,
                        action='store',
                        type=int,
                        default=512,
                        help='The block size for reading in bytes')
    parser.add_argument('-j', '--json',
                        required=False,
                        action='store',
                        help='Output to json file')
    parser.add_argument('--not_use_wmi',
                        required=False,
                        action='store_true',
                        help='Don`t use wmi counters statistics')

    parser.add_argument('--disable_read_test',
                        required=False,
                        action='store_true',
                        help='Don`t execute read test')
    parser.add_argument('--disable_copy_test',
                        required=False,
                        action='store_true',
                        help='Don`t execute copy test')
    parser.add_argument('--disable_shuffle_read_test',
                        required=False,
                        action='store_true',
                        help='Don`t execute multi-io test')

    parser.add_argument('--disable_multi_test',
                        required=False,
                        action='store_true',
                        help='Don`t execute multi-io test')

    parser.add_argument('--disable_sys_copy_test',
                        required=False,
                        action='store_true',
                        help='Don`t execute system copy file test')

    parser.add_argument('--save_test_file',
                        required=False,
                        action='store_false',
                        help='Don`t delete file created on write test')

    parser.add_argument('-t', '--wmi_test_thread_count',
                        required=False,
                        action='store',
                        type=int,
                        default=1,
                        help='Number of test thread when use wmi statistics')

    parser.add_argument('-p', '--wmi_monitoring_interval',
                        required=False,
                        action='store',
                        type=float,
                        default=0.01,
                        help='Interval get wmi statistics')

    args = parser.parse_args()

    mask = 0x1F
    if args.disable_read_test:
        mask &= 0x1E
    if args.disable_copy_test:
        mask &= 0x1D
    if args.disable_shuffle_read_test:
        mask &= 0x1B
    if args.disable_multi_test:
        mask &= 0x17
    if args.disable_sys_copy_test:
        mask &= 0xF

    args.test_mask = mask
    return args


class ComplexCounters():
    def __init__(self, *names):
        super().__init__()
        self._counters = {name: Counter(name) for name in names}
        self._names = names

    def update(self, value_object):
        for name in self._names:
            value = float(getattr(value_object, name))
            self._counters[name].update(value)

    def __str__(self):
        return '\n'.join([str(value) for value in self._counters.values()])


class Counter:

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.avg = None
        self.max = None
        self.min = None
        self.counter = 0
        self._sum = 0

    def update(self, value):
        if self.counter == 0:
            self._sum = value
            self.avg = value
            self.max = value
            self.min = value
            self.counter = 1
        else:
            self.counter += 1
            self._sum += value
            if self.min > value:
                self.min = value
            if self.max < value:
                self.max = value

    def get_result(self):
        return self.name, self._sum / self.counter, self.min, self.max

    def __str__(self):
        return f'{self.name} avg:{(self._sum / self.counter):.3f} min:{self.min:.2f} max:{self.max:.2f}'


class RunWMI:

    def __init__(self, procedure, monitoring_interval=0.01,
                 monitoring_parameters=['CurrentDiskQueueLength', 'PercentIdleTime',
                                        'AvgDisksecPerRead', 'AvgDisksecPerWrite',
                                        'AvgDiskBytesPerRead', 'AvgDiskBytesPerWrite',
                                        'AvgDiskReadQueueLength', 'AvgDiskWriteQueueLength'
                                        ],
                 thread_count=2,
                 arguments=None, keyword_arguments=None):
        super().__init__()
        self.procedure = procedure
        self.arguments = arguments
        self.keyword_arguments = keyword_arguments
        self.monitoring_interval = monitoring_interval
        self.thread_count = thread_count
        self.statistics = ComplexCounters(*monitoring_parameters)
        self.multi_results = []
        self.multi_results = []
        self.multi_results = []
        self.multi_results = []

    def execute(self):
        wmi_obj = wmi.WMI(
            moniker="winmgmts:root\cimv2"
        )

        working_threads = [Thread(target=self.procedure, args=self.arguments, kwargs=self.keyword_arguments)
                           for i in range(self.thread_count)]
        for working_thread in working_threads:
            working_thread.start()

        while all([working_thread.is_alive() for working_thread in working_threads]):
            info = wmi_obj.Win32_PerfFormattedData_PerfDisk_PhysicalDisk()[0]
            self.statistics.update(info)
            sleep(self.monitoring_interval)

        for working_thread in working_threads:
            working_thread.join()


class RunWMITest(RunWMI):

    def __init__(self, monitoring_interval=0.01,
                 monitoring_parameters=['CurrentDiskQueueLength', 'PercentIdleTime',
                                        'AvgDisksecPerRead', 'AvgDisksecPerWrite',
                                        'AvgDiskBytesPerRead', 'AvgDiskBytesPerWrite',
                                        'AvgDiskReadQueueLength', 'AvgDiskWriteQueueLength'
                                        ], thread_count=2, arguments=None, keyword_arguments=None):
        super().__init__(None, monitoring_interval, monitoring_parameters, thread_count, arguments,
                         keyword_arguments)

    def execute(self):
        wmi_obj = wmi.WMI(
            moniker="winmgmts:root\cimv2"
        )
        args = self.arguments
        tests = [Benchmark(args.file, args.size, args.write_block_size, args.read_block_size, args.test_mask,
                           run_on_create=False, clear_temp=args.save_test_file) for _ in
                 range(self.thread_count)]
        working_threads = [Thread(target=test.execute_tests)
                           for test in tests]

        for working_thread in working_threads:
            working_thread.start()

        while all([working_thread.is_alive() for working_thread in working_threads]):
            info = wmi_obj.Win32_PerfFormattedData_PerfDisk_PhysicalDisk()[0]
            self.statistics.update(info)
            #print(info)
            sleep(self.monitoring_interval)

        for working_thread in working_threads:
            working_thread.join()

        if tests:
            first_test = tests.pop(0)
            for test in tests:
                first_test.avg_with_other(test)

            first_test.print_result()


class Benchmark:

    def __init__(self, file, write_mb, write_block_kb, read_block_b, test_mask=0x111b, run_on_create=True, clear_temp=True):
        self.file = file + chr(random.randint(65, 90)) + chr(random.randint(65, 90)) + chr(random.randint(65, 90))
        self.write_mb = write_mb
        self.write_block_kb = write_block_kb
        self.read_block_b = read_block_b
        self.test_mask = test_mask
        self.clear_temp_file =clear_temp
        if run_on_create:
            self.execute_tests()
        self.copy_results = []

    def execute_tests(self):
        wr_blocks = int(self.write_mb * 1024 / self.write_block_kb)
        rd_blocks = int(self.write_mb * 1024 * 1024 / self.read_block_b)
        cp_blocks = int(self.write_mb * 1024 * 1024 / self.read_block_b)
        test_mask = self.test_mask
        self.write_results = self.write_test(1024 * self.write_block_kb, wr_blocks)
        self.read_results = self.read_test(self.read_block_b, rd_blocks) if test_mask & 0x1 else []
        self.sys_results = self.test_sys_copy() if test_mask & 0x10 else ""
        self.copy_results = self.copy_test(self.read_block_b, cp_blocks) if test_mask & 0x2 else []
        self.shufle_results = self.read_shuffle_test(self.read_block_b, rd_blocks) if test_mask & 0x4 else []
        self.multi_results = self.multi_test(self.read_block_b, cp_blocks) if test_mask & 0x8 else []

        if os.path.exists(self.file) and self.clear_temp_file:
            os.remove(self.file)
        copy_path = self.file + '.copy'
        if os.path.exists(copy_path):
            os.remove(copy_path)

    def write_test(self, block_size, blocks_count, show_progress=True):
        '''
        Tests write speed by writing random blocks, at total quantity
        of blocks_count, each at size of block_size bytes to disk.
        Function returns a list of write times in sec of each block.
        '''
        f = os.open(self.file, os.O_CREAT | os.O_WRONLY, 0o777)  # low-level I/O

        took = []
        for i in range(blocks_count):
            if show_progress:
                # dirty trick to actually print progress on each iteration
                sys.stdout.write('\rWriting: {:.2f} %'.format(
                    (i + 1) * 100 / blocks_count))
                sys.stdout.flush()
            buff = os.urandom(block_size)
            start = time()
            os.write(f, buff)
            os.fsync(f)  # force write to disk
            t = time() - start
            took.append(t)

        os.close(f)
        if show_progress:
            print("\rWrite Test Complete!")

        return took

    def test_sys_copy(self):
        start_time = time()
        print(self.file)
        # subprocess.run(["copy", self.file, f"{self.file}.copy"] )
        os.system(f"copy {self.file} {self.file}.copy  /Y")
        time_it = time() - start_time
        return f"\n\nSystem copy tool tims {time_it:.2f}s speed:{sizefmt(self.write_mb * 1024 * 1024 / time_it)}/s"

    def read_test(self, block_size, blocks_count, show_progress=True):
        '''
        Performs read speed test by reading random offset blocks from
        file, at maximum of blocks_count, each at size of block_size
        bytes until the End Of File reached.
        Returns a list of read times in sec of each block.
        '''
        f = os.open(self.file, os.O_RDONLY, 0o777)  # low-level I/O
        # generate random read positions
        offsets = list(range(0, blocks_count * block_size, block_size))
        took = []
        for i, offset in enumerate(offsets, 1):
            if show_progress and i % int(self.write_block_kb * 1024 / self.read_block_b) == 0:
                # read is faster than write, so try to equalize print period
                sys.stdout.write('\rReading: {:.2f} %'.format(
                    (i + 1) * 100 / blocks_count))
                sys.stdout.flush()
            start = time()
            # os.lseek(f, offset, os.SEEK_SET)  # set position
            buff = os.read(f, block_size)  # read from position

            t = time() - start
            # if not buff: break  # if EOF reached
            took.append(t)

        os.close(f)
        if show_progress:
            print("\rRead Test Complete!")
        return took

    def read_shuffle_test(self, block_size, blocks_count, show_progress=True):
        '''
        Performs read speed test by reading random offset blocks from
        file, at maximum of blocks_count, each at size of block_size
        bytes until the End Of File reached.
        Returns a list of read times in sec of each block.
        '''
        f = os.open(self.file, os.O_RDONLY, 0o777)  # low-level I/O
        # generate random read positions
        offsets = list(range(0, blocks_count * block_size, block_size))
        shuffle(offsets)

        took = []
        for i, offset in enumerate(offsets, 1):
            if show_progress and i % int(self.write_block_kb * 1024 / self.read_block_b) == 0:
                # read is faster than write, so try to equalize print period
                sys.stdout.write('\rShuffle: {:.2f} %'.format(
                    (i + 1) * 100 / blocks_count))
                sys.stdout.flush()
            start = time()
            os.lseek(f, offset, os.SEEK_SET)  # set position
            buff = os.read(f, block_size)  # read from position

            t = time() - start
            # if not buff: break  # if EOF reached
            took.append(t)

        os.close(f)
        if show_progress:
            print("\rShuffle Test Complete!")
        return took

    def get_result_string(self, results, block_size_b, test_size, test_name):
        if not results:
            return ''

        test_time = sum(results)
        size = block_size_b * len(results)
        max_time = block_size_b / (min(results))
        min_time = block_size_b / (max(results))
        speed = size / test_time
        return f'\n\n{test_name} {sizefmt(size)} in  {test_time:.4f} s\n{test_name} speed is  {sizefmt(speed)}/s' \
               f'\n  max: {sizefmt(max_time)}/s, min: {sizefmt(min_time)}/s  \n'

    def multi_test(self, block_size, blocks_count, show_progress=True):
        '''
        Performs read speed test by reading random offset blocks from
        file, at maximum of blocks_count, each at size of block_size
        bytes until the End Of File reached.
        Returns a list of read times in sec of each block.
        '''

        r = os.open(self.file, os.O_RDONLY, 0o777)  # low-level
        w = os.open(self.file + '.copy', os.O_CREAT | os.O_WRONLY, 0o777)  # I/O
        took = []
        # os.lseek(r, 0, os.SEEK_SET)
        offsets = list(range(0, blocks_count * block_size, block_size))
        shuffle(offsets)
        for i, offset in enumerate(offsets, 1):
            if show_progress and i % int(self.write_block_kb * 1024 / self.read_block_b) == 0:
                # read is faster than write, so try to equalize print period
                sys.stdout.write('\rMultiIO: {:.2f} %'.format(
                    (i + 1) * 100 / blocks_count))
                sys.stdout.flush()
            start = time()
            buff = os.read(r, block_size)  # read from position
            os.lseek(r, offset, os.SEEK_SET)
            os.lseek(w, offset, os.SEEK_SET)
            # os.lseek(r, i * block_size, os.SEEK_SET)
            os.write(w, buff)
            os.fsync(w)  # fo
            t = time() - start
            took.append(t)

        os.close(r)
        os.close(w)
        if show_progress:
            print("\rMultiIO Test Complete!")
        return took

    def copy_test(self, block_size, blocks_count, show_progress=True):
        '''
        Performs read speed test by reading random offset blocks from
        file, at maximum of blocks_count, each at size of block_size
        bytes until the End Of File reached.
        Returns a list of read times in sec of each block.
        '''
        took = []
        with open(self.file, mode="rb") as r, open(self.file + '.copy', mode="wb") as w:

            for i in range(0, blocks_count):
                if show_progress and i % int(self.write_block_kb * 1024 / self.read_block_b) == 0:
                    # read is faster than write, so try to equalize print period
                    sys.stdout.write('\rCopy: {:.2f} %'.format(
                        (i + 1) * 100 / blocks_count))
                    sys.stdout.flush()
                start = time()
                buff = r.read(block_size)
                w.write(buff)
                w.flush()
                t = time() - start
                took.append(t)
        if show_progress:
            print("\rCopy Test Complete!")
        return took

    def print_result(self, write_report=True):
        result = self.get_result_string(self.write_results, self.write_block_kb * 1024, self.write_mb, "Write")
        result += self.get_result_string(self.read_results, self.read_block_b, self.write_mb, "Read")
        result += self.get_result_string(self.copy_results, self.read_block_b, self.write_mb, "Copy")
        result += self.get_result_string(self.shufle_results, self.read_block_b, self.write_mb, "Shuffle Read")
        result += self.get_result_string(self.multi_results, self.read_block_b, self.write_mb, "Multi")
        result += self.sys_results
        print(result)
        if write_report:
            with open(f"report_{platform.node()}.txt", "wt") as f:
                f.write(result)

    def get_json_result(self, output_file):
        results_json = {}
        results_json["Written MB"] = self.write_mb
        results_json["Write time (sec)"] = round(sum(self.write_results), 2)
        results_json["Write speed in MB/s"] = round(self.write_mb / sum(self.write_results), 2)
        results_json["Read blocks"] = len(self.read_results)
        results_json["Read time (sec)"] = round(sum(self.read_results), 2)
        results_json["Read speed in MB/s"] = round(self.write_mb / sum(self.read_results), 2)
        with open(output_file, 'w') as f:
            json.dump(results_json, f)

    def avg_with_other(self, other_test):
        if self.read_results and other_test.read_results:
            self.read_results.extend(other_test.read_results)
        if self.write_results and other_test.write_results:
            self.write_results.extend(other_test.write_results)
        if self.copy_results and other_test.copy_results:
            self.copy_results.extend(other_test.copy_results)
        if self.multi_results and other_test.multi_results:
            self.multi_results.extend(other_test.multi_results)
        if self.shufle_results and other_test.shufle_results:
            self.shufle_results.extend(other_test.shufle_results)

        self.write_mb += other_test.write_mb


def main_test(args):
    benchmark = Benchmark(args.file, args.size, args.write_block_size, args.read_block_size, args.test_mask,
                          clear_temp=args.save_test_file)
    if args.json is not None:
        benchmark.get_json_result(args.json)
    else:
        benchmark.print_result()


def wmi_test(args):
    benchmark = Benchmark(args.file, args.size, args.write_block_size, args.read_block_size, args.test_mask,
                          clear_temp=args.save_test_file)
    benchmark.print_result()


def main():
    args = get_args()
    if not args.not_use_wmi:
        test = RunWMITest(monitoring_interval=args.wmi_monitoring_interval,
                          monitoring_parameters=['CurrentDiskQueueLength', 'PercentIdleTime',
                                                 'AvgDisksecPerRead', 'AvgDisksecPerWrite',
                                                 'AvgDiskBytesPerRead', 'AvgDiskBytesPerWrite',
                                                 'AvgDiskReadQueueLength', 'AvgDiskWriteQueueLength'
                                                 ], thread_count=args.wmi_test_thread_count, arguments=args)
        test.execute()
        print(test.statistics)
        with open(f"report_{platform.node()}.txt", "at") as f:
            f.write("\n")
            f.write(str(test.statistics))

    else:
        main_test(args)


if __name__ == "__main__":
    main()
