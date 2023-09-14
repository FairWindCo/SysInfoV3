import datetime
import os
import sys
from shutil import rmtree
from threading import Thread


def clear_mai_folder(dir_mei, current_mei, min_old_time=600, debug=False):
    check_time = datetime.datetime.timestamp(datetime.datetime.now())
    for file in os.listdir(dir_mei):
        if debug:
            print(f"check {file}")
        if file.startswith("_MEI") and not file.endswith(current_mei):
            try:
                full_path = os.path.join(dir_mei, file)
                # print(check_time)
                # print(os.stat(full_path).st_mtime)
                old_time = check_time - os.stat(full_path).st_mtime
                if debug:
                    print(f"CHECK {full_path}, {old_time}")
                if old_time > min_old_time:
                    if debug:
                        print(f"DELETE {full_path}")
                    rmtree(full_path)
            except PermissionError:  # mainly to allow simultaneous pyinstaller instances
                if debug:
                    print(f"permissions error {file}")
                pass
            except OSError as e:  # mainly to allow simultaneous pyinstaller instances
                if debug:
                    print(f"os error on {file} {e}")
                pass



def cleanup_mei(min_old_time=600, debug=False):
    """
    Rudimentary workaround for https://github.com/pyinstaller/pyinstaller/issues/2379
    """
    try:
        mei_bundle = getattr(sys, "_MEIPASS", False)
        # print(f"ME:{mei_bundle}")
        if mei_bundle:
            dir_mei, current_mei = mei_bundle.split("_MEI")
            clear_mai_folder(dir_mei, current_mei, min_old_time, debug=debug)
            clear_mai_folder("c:\\windows\\temp", current_mei, min_old_time, debug=debug)
    except Exception as e:
        if debug:
            print(type(e), e)
        pass


def cleanup_mei_threading(debug=False):
    thread = Thread(target=cleanup_mei, daemon=True, kwargs={'debug': debug})
    thread.start()
    return thread
