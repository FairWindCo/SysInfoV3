import os
import re
import subprocess


def get_full_paths(db_path):
    result = []
    if os.path.exists(db_path):
        if os.path.isfile(db_path):
            result.append(db_path)
        elif os.path.isdir(db_path):
            for (dirpath, dirnames, filenames) in os.walk(db_path):
                for filename in filenames:
                    spath = os.path.join(dirpath, filename)
                    if os.path.splitext(spath)[-1] == '.py':
                        print(spath)
                        result.append(spath)
    return result


def get_full_paths_dict(db_path):
    result = dict()
    if os.path.exists(db_path):
        if os.path.isfile(db_path):
            file_name = os.path.basename(db_path)
            result[file_name] = db_path
        elif os.path.isdir(db_path):
            for (dirpath, dirnames, filenames) in os.walk(db_path):
                for filename in filenames:
                    spath = os.path.join(dirpath, filename)
                    if os.path.splitext(spath)[-1] == '.py':
                        print(spath)
                        result[filename] = spath
    return result


def get_imports(file_name, import_set=None, encoding=None):
    if import_set is None:
        import_set = set()
    f = open(file_name, "rt", encoding=encoding)
    try:
        reg = re.compile(r"^\s*(from|import)\s*(.?\w[\w\d]*)")
        lines = f.readlines()
        for line in lines:
            finded = reg.search(line)
            if finded:
                import_set.add(finded.group(2))
    finally:
        f.close()
    return import_set


def process_one_import_path(current_path, script_path_set, add_import_set):
    print(current_path)
    file_script_path = "{}.py".format(current_path)
    if os.path.isfile(file_script_path):
        try:
            for encode in ['utf', 'cp1251', 'cp866']:
                add_import_set = get_imports(file_script_path, add_import_set, encode)
                break
        except UnicodeDecodeError:
            pass
        script_path_set.add(file_script_path)
    elif os.path.isdir(current_path):
        init_file_path = os.path.join(current_path, '__init__.py')
        if os.path.exists(init_file_path):
            add_import_set = get_imports(init_file_path, add_import_set)
            script_path_set.add(init_file_path)
        for (dirpath, _, filenames) in os.walk(current_path):
            for filename in filenames:
                spath = os.path.join(dirpath, filename)
                if os.path.splitext(spath)[-1] == '.py':
                    script_path_set.add(spath)
                    try:
                        add_import_set = get_imports(spath, add_import_set)
                    except UnicodeDecodeError:
                        print("ERR")
                        for encode in ['cp1251', 'cp1252', 'cp850', 'cp866']:
                            try:
                                add_import_set = get_imports(spath, add_import_set, encode)
                            except UnicodeDecodeError:
                                pass

    return add_import_set


def form_script_imports(script_name, script_base_path):
    if type(script_name) == str:
        import_set = get_imports(script_name)
    else:
        import_set = set()
        for name in script_name:
            import_set = get_imports(name, import_set)

    full_import_set = import_set
    script_path_set = set()
    while import_set:
        add_import_set = set()
        for one_import in import_set:
            one_import_path = os.path.join(script_base_path, *(one_import.split('.')))
            process_one_import_path(one_import_path, script_path_set, add_import_set)
            one_import_path = os.path.join(script_base_path, 'site-packages', *(one_import.split('.')))
            process_one_import_path(one_import_path, script_path_set, add_import_set)
        import_set = add_import_set.difference(full_import_set)
        full_import_set.update(import_set)
        print(len(full_import_set), import_set)
    return full_import_set, script_path_set


def compile_exe(script_name, python_path=r'C:\Program Files\IronPython 3.4'):
    compiler_path = '{}'.format(os.path.join(python_path, 'ipyc.exe'))
    # library_path = os.path.join(python_path, 'Lib')
    library_path = os.path.join(python_path, r'Lib')
    #library_path = r'venv\Lib\site-packages'
    if type(script_name) == str:
        params = [compiler_path, "/main:{}".format(script_name)]
        if os.path.exists(script_name[:-3] + '.exe'):
            exe_time = os.path.getmtime(script_name[:-3] + '.exe')
            code_time = os.path.getmtime(script_name)
            if exe_time > code_time:
                print("SKIP CREATE EXE FOR ", script_name)
                return
    else:
        main_script = script_name[0]
        other_scripts = script_name[1:]
        params = [compiler_path, "/main:{}".format(main_script)]
        params.extend(other_scripts)
        if os.path.exists(main_script[:-3] + '.exe'):
            exe_time = os.path.getmtime(main_script[:-3] + '.exe')
            no_need_compile = True
            for script in script_name:
                no_need_compile &= exe_time > os.path.getmtime(script)
            if no_need_compile:
                print("SKIP CREATE EXE FOR ", main_script)
                return

    need_modules, lib_path = form_script_imports(script_name, library_path)
    # for one_lib_path in lib_path:
    #     params.append("'{}'".format(one_lib_path))
    # params.extend(lib_path)
    compiler_params_file = "compiler_params.txt"
    with open(compiler_params_file, "wt") as f:
        for lib in lib_path:
            f.write(f"{lib}\r")
    params.append("@" + compiler_params_file)
    params.append("/target:exe")
    params.append("/platform:x86")
    # params.append("/standalone")
    params.append("/embed")
    compile_string = " ".join(params)
    print(":>", compile_string)
    print(subprocess.call(params))
    #os.remove(compiler_params_file)


if __name__ == "__main__":
    compile_exe(["system_info.py", "old_utility.py"])
