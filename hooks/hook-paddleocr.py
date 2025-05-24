from PyInstaller.utils.hooks import collect_data_files, collect_all, collect_dynamic_libs

datas = collect_data_files("paddleocr", include_py_files=True)
binaries = collect_dynamic_libs("paddleocr")