import configparser

from constants import CONFIG_PATH

config = configparser.ConfigParser()
config.read(CONFIG_PATH, encoding='utf-8')

def get_config(section, option, default=None):
    """获取配置项的值"""
    try:
        value = config.get(section, option)
        return value if value else default
    except configparser.NoOptionError:
        print(f"配置项 '{option}' 在节 '{section}' 中不存在。")
        return None
    except configparser.NoSectionError:
        print(f"节 '{section}' 不存在。")
        return None

def set_config(section, option, value):
    """设置配置项的值"""
    # print(config.has_section(section))
    # if not config.has_section(section):
    #     config.add_section(section)
    config.set(section, option, value)
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)