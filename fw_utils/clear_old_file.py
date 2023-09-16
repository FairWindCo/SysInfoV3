import logging
import os
import re
import time


def clear_old_backup(scan_dir: str, pattern: str = '.*', age_days: int = 7, minimal_safe_files: int = 0,
                     dont_delete_file: str = None):
    result = True
    days_before = (time.time() - age_days * 86400)
    template = re.compile(pattern)
    files_lists = {}
    for f in os.listdir(scan_dir):
        if template.match(f):
            file_path = os.path.join(scan_dir, f)
            files_lists[os.stat(file_path).st_mtime] = file_path
    logging.debug(f"list found files: {files_lists}")
    if len(files_lists) > minimal_safe_files:
        for stat_time, file_path in files_lists.items():
            if stat_time < days_before and file_path != dont_delete_file:
                try:
                    os.remove(file_path)
                except Exception as io:
                    logging.error(f"delete file {file_path} error: {io}")
                    result = False
    return result
