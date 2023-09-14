from __future__ import annotations

import logging
import os
import platform
import subprocess
from datetime import datetime
from zipfile import ZipFile

from fw_server_communications.mail_reports import send_mail
from fw_server_communications.inventory_communications import send_report_error


def get_full_paths(db_paths):
    result = []
    total_size = 0
    if isinstance(db_paths, str):
        db_paths = [db_paths]
    for db_path in db_paths:
        if os.path.exists(db_path):
            if os.path.isfile(db_path):
                result.append(db_path)
                fsize = os.path.getsize(db_path)
                total_size += fsize
                logging.info("{} : {:.2f}Gb".format(db_path, (fsize / GIGABYTE)))
            elif os.path.isdir(db_path):
                for (dirpath, dirnames, filenames) in os.walk(db_path):
                    for filename in filenames:
                        spath = os.path.join(dirpath, filename)
                        fsize = os.path.getsize(spath) / GIGABYTE
                        logging.info("{} : {:.2f}Gb".format(spath, fsize))
                        total_size += fsize
                        result.append(spath)
    logging.info(total_size)
    return result, total_size


def archive_file_rar(path_to_archive, dst_path, winrar_path, path_list, config):
    exec_rar = 0
    try:
        rar_command_arguments = config.get('rar_command_arguments', 'a -dh')
        for file_path in path_to_archive:
            commands = [winrar_path]
            if rar_command_arguments:
                commands.extend(rar_command_arguments.split(' '))
            commands.append(dst_path)
            commands.append(file_path)
            logging.info(commands)
            exec_rar += (1 if subprocess.call(
                # [winrar_path, 'a', '-dh', dst_path, file_path]
                commands
            ) == 0 else 0)
        if exec_rar < len(path_list):
            send_report_error("NOT ALL FILE ARCHIVED", config)
    except Exception as e:
        send_report_error(f'EXEC ERROR: {e}', config)


def archive_file_zip(path_to_archive, dst_path, config):
    ZIP_COMPRESSION = config.get('zip_compression', 8)
    try:
        zipObj = ZipFile(dst_path, 'w', compression=ZIP_COMPRESSION, allowZip64=True)
        try:
            for file_path in path_to_archive:
                zipObj.write(file_path)
        finally:
            zipObj.close()
    except Exception as e:
        send_report_error(f"ZIP ERROR {e}", config)


def get_result_file_name(winrar_path, is_template=False, config=None):
    if config is None:
        config = {}
    host_name = platform.node()
    BKP_FORMAT = config.get('bkp_file_format', '{}zvit{}.rar')
    if not winrar_path:
        BKP_FORMAT = BKP_FORMAT.replace('.rar', '.zip')
    else:
        BKP_FORMAT = BKP_FORMAT.replace('.rar', '.' + config.get('rar_file_extensions', 'rar'))
    date_str = '[0-9]{6}\\' if is_template else datetime.now().strftime("%d%m%y")
    return BKP_FORMAT.format(host_name, date_str)


def get_result_path(winrar_path, config):
    TMP_BKP = config.get('db_path', '.')
    bkp_file_name = get_result_file_name(winrar_path, False, config)
    if os.path.exists(TMP_BKP) and os.path.isdir(TMP_BKP):
        s_path = os.path.join(TMP_BKP, bkp_file_name)
        logging.debug(s_path)
        return s_path
    return None


def archive_file(path_to_archive, dst_path, winrar_path, path_lst, config):
    if path_to_archive:
        if winrar_path:
            archive_file_rar(path_to_archive, dst_path, winrar_path, path_lst, config)
        else:
            archive_file_zip(path_to_archive, dst_path, config)
    else:
        send_mail("NO DB FILE", config)


GIGABYTE = float(1024 ** 3)
