# hook-tqdm.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("tqdm")
hiddenimports = collect_submodules("tqdm")