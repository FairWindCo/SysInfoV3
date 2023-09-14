import re

import pywintypes
import win32com.client as win32
import win32net
import win32security

import fw_isodurations
from fw_windows_sys_info.sheduller.actions import get_action_def, IComHandlerAction
from fw_windows_sys_info.sheduller.triggers import construct_trigger

TASK_ENUM_HIDDEN = 0x1


def is_system_task(name, task_def):
    if task_def.get('is_dcom', False):
        return True
    check_name = name.lower()
    if check_name.startswith('user_feed_synchronization'):
        return True
    if check_name.startswith('windows defender'):
        return True
    author = task_def['author']
    if author:
        author_lower = author.lower()
        if author_lower.find('microsoft') >= 0 or author_lower.find('микрософт') >= 0:
            return True
    path = task_def['main_path'].lower()
    if path.startswith('%systemroot%'):
        return True
    if path.startswith('%windir%'):
        return True


def get_tasks(show_hidden=False, hide_system=True, hide_dcom=True):
    # https://github.com/Alexpux/mingw-w64/blob/master/mingw-w64-headers/include/taskschd.h
    # https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-triggers-tasktype-element
    # https://learn.microsoft.com/en-us/windows/win32/taskschd/trigger
    # https://stackoverflow.com/questions/70963769/how-to-access-windows-scheduler-actions-with-python-and-win32com
    def get_task_state(state):
        TASK_STATE_UNKNOWN = 0
        TASK_STATE_DISABLED = 1
        TASK_STATE_QUEUED = 2
        TASK_STATE_READY = 3
        TASK_STATE_RUNNING = 4
        if state == TASK_STATE_UNKNOWN:
            return 'UNKNOWN'
        if state == TASK_STATE_DISABLED:
            return 'DISABLED'
        if state == TASK_STATE_QUEUED:
            return 'QUEUED'
        if state == TASK_STATE_READY:
            return 'READY'
        if state == TASK_STATE_RUNNING:
            return 'RUNNING'
        return f'UNKNOWN{state}'

    users_sid = {}

    scheduler = win32.dynamic.Dispatch('Schedule.Service')
    scheduler.Connect()
    folders = [scheduler.GetFolder('\\')]  # \ - is root folder
    tasks = []
    name_cleaner = re.compile('.*(-[A-F0-9]{2,})')
    while folders:
        folder = folders.pop(0)
        folders += list(folder.GetFolders(0))  # 0 - is reserved flag
        for task in folder.GetTasks(TASK_ENUM_HIDDEN if show_hidden else 0):
            user_id = task.Definition.Principal.UserId
            uuid = ''
            if user_id:
                uuid = users_sid.get(user_id, None)
                if uuid is None:
                    try:
                        user_str = win32net.NetUserGetInfo(None, user_id, 4)
                        uuid = win32security.ConvertSidToStringSid(user_str['user_sid'])
                    except pywintypes.error:
                        uuid = ''
                    users_sid[user_id] = uuid
            name = task.Name

            if uuid:
                name = name.replace(uuid, '<User>')
                is_for_user_task = True
            else:
                is_for_user_task = False
            res = name_cleaner.match(name)
            if res:
                name = name[:res.regs[1][0]]

            task_list = [get_action_def(action) for action in task.Definition.Actions]
            triggers_list = [construct_trigger(collection) for collection in
                             task.Definition.Triggers]
            run_time = task.NextRunTime.strftime("%Y%m%d%H%M%S.%f%z") if task.NextRunTime else ''
            last_run = task.LastRunTime.strftime("%Y%m%d%H%M%S.%f%z") if task.LastRunTime else ''
            dcom_task = isinstance(task_list[0], IComHandlerAction)
            if hide_dcom and dcom_task:
                continue
            reg_date = str(task.Definition.RegistrationInfo.Date)
            reg_date = fw_isodurations.parse_datetime(reg_date).strftime("%Y%m%d%H%M%S.%f%z") if reg_date else ''
            global_task_def = {
                'name': name,
                'task_for_user': is_for_user_task,
                'next_run': run_time,
                'status': get_task_state(task.State),
                'last_run': last_run,
                'last_result': task.LastTaskResult,
                'uuid': uuid,
                'author': task.Definition.RegistrationInfo.Author,
                'comment': task.Definition.RegistrationInfo.Description,
                'runas': user_id,
                'start_time': reg_date,
                'schedule_type': ';'.join(map(str, triggers_list)),
                'main_path': task_list[0].short(),
                'full_actions': ';'.join(map(str, task_list)),
                'is_dcom': dcom_task,
                'is_multi': len(task_list) > 1,
                'actions': list(map(lambda a: a.as_dict(), task_list))
            }
            system_task = is_system_task(name, global_task_def)
            if hide_system and system_task:
                continue
            global_task_def['is_system'] = system_task
            tasks.append(global_task_def)
    return tasks


if __name__ == "__main__":
    tasks = get_tasks()
    print(tasks)
    for task in tasks:
        print(task['name'], task['schedule_type'], task['main_path'], task['last_run'])
