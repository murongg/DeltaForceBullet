from PyInstaller.utils.hooks import collect_data_files, collect_all

datas = collect_data_files("Cython", include_py_files=True)