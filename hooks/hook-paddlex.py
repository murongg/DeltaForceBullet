from PyInstaller.utils.hooks import collect_data_files

# 自动收集 paddlex 的数据文件（包括 .version）
datas = collect_data_files("paddlex")