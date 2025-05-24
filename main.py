import logging
import sys

import keyboard
import win32api
import win32con
import win32gui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton,
                             QVBoxLayout, QHBoxLayout, QTextEdit, QGroupBox, QFormLayout, QSpinBox, QLabel,
                             QRadioButton, QMessageBox, QCheckBox)

from bullet import Bullet
from config import get_config, set_config
from constants import ICON_PATH
from logger import LogDisplayController, configure_log_system

class WindowSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.max_bullet_price = None
        self.min_bullet_price = None
        self.direct_buy_max_bullet_price = None
        self.selected_window_id = None
        self.bullet = Bullet(self)
        self.timer = QTimer()
        self.initUI()
        self.set_logger()
        self.logger = logging.getLogger("app")
        self.init_config()

        keyboard.add_hotkey("ctrl+1", lambda: self.bullet.start())
        keyboard.add_hotkey("ctrl+2", lambda: self.bullet.stop())

    def initUI(self):
        # 设置布局
        window_set_group = QGroupBox("窗口设置")
        button_layout = QHBoxLayout()
        self.btnA = QPushButton('选择检测端窗口')
        self.btnB = QPushButton('选择购买端窗口')
        button_layout.addWidget(self.btnA, stretch=1)
        button_layout.addWidget(self.btnB, stretch=1)
        window_set_group.setLayout(button_layout)

        params_group = QGroupBox("参数")
        params_layout = QFormLayout()
        params_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        bullet_price_layout = QHBoxLayout()
        self.min_bullet_price = QSpinBox()
        self.min_bullet_price.setMaximum(100000)
        self.min_bullet_price.setMinimum(1)
        self.max_bullet_price = QSpinBox()
        self.max_bullet_price.setMaximum(100000)
        self.max_bullet_price.setMinimum(1)
        bullet_price_layout.addWidget(self.min_bullet_price, stretch=1)
        bullet_price_layout.addWidget(QLabel("~"))
        bullet_price_layout.addWidget(self.max_bullet_price, stretch=1)
        bullet_price_layout.setAlignment(Qt.AlignHCenter)
        bullet_price_layout.setAlignment(Qt.AlignVCenter)
        params_layout.addRow("子弹价格", bullet_price_layout)

        direct_buy_bullet_price_layout = QHBoxLayout()
        self.direct_buy_min_bullet_price = QSpinBox()
        self.direct_buy_min_bullet_price.setMaximum(100000)
        self.direct_buy_min_bullet_price.setMinimum(1)
        self.direct_buy_max_bullet_price = QSpinBox()
        self.direct_buy_max_bullet_price.setMaximum(100000)
        self.direct_buy_max_bullet_price.setMinimum(1)
        direct_buy_bullet_price_layout.addWidget(self.direct_buy_min_bullet_price, stretch=1)
        direct_buy_bullet_price_layout.addWidget(QLabel("~"))
        direct_buy_bullet_price_layout.addWidget(self.direct_buy_max_bullet_price, stretch=1)
        direct_buy_bullet_price_layout.setAlignment(Qt.AlignHCenter)
        direct_buy_bullet_price_layout.setAlignment(Qt.AlignVCenter)
        # params_layout.addRow("直接购买子弹价格", direct_buy_bullet_price_layout)

        self.formula_max_price = QSpinBox()
        self.formula_max_price.setMaximum(100000)
        self.formula_max_price.setMinimum(1)
        params_layout.addRow("档屎价格", self.formula_max_price)

        self.expect_sell_price = QSpinBox()
        self.expect_sell_price.setMaximum(100000)
        self.expect_sell_price.setMinimum(1)
        params_layout.addRow("预期卖出价格", self.expect_sell_price)


        feature_group = QGroupBox("功能选择")
        feature_layout = QHBoxLayout()
        self.feature_formula_ds = QCheckBox('启用档屎功能')
        self.feature_formula_ds.setChecked(False)
        self.feature_buy_direct = QCheckBox('启用直接购买')
        self.feature_buy_direct.setChecked(False)
        self.feature_rolling = QCheckBox('启用滚仓功能')
        self.feature_rolling.setChecked(False)
        feature_layout.addWidget(self.feature_formula_ds, stretch=1)
        feature_layout.addStretch(1)
        # feature_layout.addWidget(self.feature_buy_direct, stretch=1)
        # feature_layout.addStretch(1)
        feature_layout.addWidget(self.feature_rolling, stretch=1)
        feature_layout.addStretch(1)
        feature_group.setLayout(feature_layout)

        formula_layout = QHBoxLayout()
        self.formula_1_bullet_count = QSpinBox()
        self.formula_1_bullet_count.setMaximum(100000)
        self.formula_1_bullet_count.setMinimum(1)

        self.formula_2_bullet_count = QSpinBox()
        self.formula_2_bullet_count.setMaximum(100000)
        self.formula_2_bullet_count.setMinimum(1)

        self.formula_3_bullet_count = QSpinBox()
        self.formula_3_bullet_count.setMaximum(100000)
        self.formula_3_bullet_count.setMinimum(1)

        self.formula_4_bullet_count = QSpinBox()
        self.formula_4_bullet_count.setMaximum(100000)
        self.formula_4_bullet_count.setMinimum(1)

        formula_layout.addWidget(self.formula_1_bullet_count)
        formula_layout.addWidget(self.formula_2_bullet_count)
        formula_layout.addWidget(self.formula_3_bullet_count)
        formula_layout.addWidget(self.formula_4_bullet_count)

        params_layout.addRow("配装子弹数量", formula_layout)
        params_group.setLayout(params_layout)

        select_formula_group = QGroupBox("需要购买的配装")
        select_formula_layout = QHBoxLayout()
        self.select_formula_1 = QRadioButton('配装1')
        self.select_formula_2 = QRadioButton('配装2')
        self.select_formula_3 = QRadioButton('配装3')
        self.select_formula_4 = QRadioButton('配装4')
        select_formula_layout.addWidget(self.select_formula_1, stretch=1)
        select_formula_layout.addWidget(self.select_formula_2, stretch=1)
        select_formula_layout.addWidget(self.select_formula_3, stretch=1)
        select_formula_layout.addWidget(self.select_formula_4, stretch=1)
        select_formula_layout.addStretch(2)
        select_formula_layout.setAlignment(Qt.AlignHCenter)
        select_formula_group.setLayout(select_formula_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(window_set_group)
        main_layout.addWidget(params_group)
        main_layout.addWidget(feature_group)
        main_layout.addWidget(select_formula_group)

        operate_group = QGroupBox("操作")
        operate_layout = QHBoxLayout()
        self.start_btn = QPushButton('开始（ctrl+1）')
        self.stop_btn = QPushButton('停止（ctrl+2）')
        operate_group.setLayout(operate_layout)
        operate_layout.addWidget(self.start_btn, stretch=1)
        operate_layout.addWidget(self.stop_btn, stretch=1)
        main_layout.addWidget(operate_group)

        self.info_display = QTextEdit()
        info_group = QGroupBox("程序日志")
        info_group.setLayout(QVBoxLayout())
        info_group.layout().addWidget(self.info_display)
        main_layout.addWidget(info_group)

        self.setLayout(main_layout)
        self.setWindowTitle('牛角洲倒子弹大师v0.2 交流QQ群：885499673')
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setGeometry(300, 300, 500, 600)

        # 连接信号槽
        self.__connect_signal_to_slot__()

    def init_config(self):
        formula_max_price = get_config("DEFAULT", "formula_max_price")
        self.formula_max_price.setValue(int(formula_max_price))
        min_bullet_price = get_config("DEFAULT", "min_bullet_price")
        self.min_bullet_price.setValue(int(min_bullet_price))
        max_bullet_price = get_config("DEFAULT", "max_bullet_price")
        self.max_bullet_price.setValue(int(max_bullet_price))
        formula_1_bullet_count = get_config("DEFAULT", "formula_1_bullet_count")
        self.formula_1_bullet_count.setValue(int(formula_1_bullet_count))
        formula_2_bullet_count = get_config("DEFAULT", "formula_2_bullet_count")
        self.formula_2_bullet_count.setValue(int(formula_2_bullet_count))
        formula_3_bullet_count = get_config("DEFAULT", "formula_3_bullet_count")
        self.formula_3_bullet_count.setValue(int(formula_3_bullet_count))
        formula_4_bullet_count = get_config("DEFAULT", "formula_4_bullet_count")
        self.formula_4_bullet_count.setValue(int(formula_4_bullet_count))
        formula_need_to_buy = get_config("DEFAULT", "formula_need_to_buy")
        self.set_formula_need_to_buy_state(formula_need_to_buy)
        feature_formula_ds = get_config("FEATURE", "formula_ds", 0)
        feature_buy_direct = get_config("FEATURE", "direct_buy", 0)
        feature_rolling = get_config("FEATURE", "rolling", 0)
        self.feature_formula_ds.setChecked(feature_formula_ds == "1")
        self.feature_buy_direct.setChecked(feature_buy_direct == "1")
        self.feature_rolling.setChecked(feature_rolling == "1")
        direct_buy_min_bullet_price = get_config("DEFAULT", "direct_buy_min_bullet_price")
        self.direct_buy_min_bullet_price.setValue(int(direct_buy_min_bullet_price))
        direct_buy_max_bullet_price = get_config("DEFAULT", "direct_buy_max_bullet_price")
        self.direct_buy_max_bullet_price.setValue(int(direct_buy_max_bullet_price))
        expect_sell_price = get_config("DEFAULT", "expect_sell_price")
        self.expect_sell_price.setValue(int(expect_sell_price))

    def set_logger(self):
        # 设置日志窗口
        try:
            self.log_controller = LogDisplayController(self.info_display)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"日志初始化失败: {str(e)}")
            self.close()

    def start_selection(self, window_id):
        """启动窗口选择流程"""
        self.selected_window_id = window_id
        self.logger.info(f"请用鼠标点击要选择的{window_id}窗口...")
        self.timer.start(50)  # 每50ms检测一次鼠标状态

    def detect_click(self):
        """检测鼠标点击事件"""
        if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
            self.timer.stop()
            x, y = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint((x, y))

            # 排除自身窗口
            if self.is_self_window(hwnd):
                self.logger.info("请选择其他应用程序窗口")
                return

            self.show_window_info(hwnd)

    def is_self_window(self, hwnd):
        """检查是否为程序自身窗口"""
        self_hwnd = int(self.winId())
        parent = win32gui.GetParent(hwnd)
        return hwnd == self_hwnd or parent == self_hwnd

    def show_window_info(self, hwnd):
        """显示窗口信息"""
        try:
            window_info = self.bullet.set_window_a_info(hwnd) if self.selected_window_id == "A" else self.bullet.set_window_b_info(hwnd)
            title = window_info.get('title')
            cls_name = window_info.get('cls_name')
            [left, top, _, _] = window_info.get('self')
            width = window_info.get('width')
            height = window_info.get('height')

            info = (
                f"窗口{self.selected_window_id}信息：\n"
                f"句柄: 0x{hwnd:X}\n"
                f"标题: {title}\n"
                f"类名: {cls_name}\n"
                f"位置: ({left}, {top})\n"
                f"尺寸: {width}x{height}\n"
                "------------------------"
            )


            self.logger.info(info)
        except Exception as e:
            self.logger.error(f"获取信息失败: {str(e)}")
            raise e

    def __connect_signal_to_slot__(self):
        """连接信号"""
        self.btnA.clicked.connect(lambda: self.start_selection('A'))
        self.btnB.clicked.connect(lambda: self.start_selection('B'))
        self.timer.timeout.connect(self.detect_click)
        self.formula_max_price.textChanged.connect(self.set_formula_max_price)
        self.min_bullet_price.textChanged.connect(self.set_min_bullet_price)
        self.max_bullet_price.textChanged.connect(self.set_max_bullet_price)
        self.formula_1_bullet_count.textChanged.connect(self.set_formula_1_bullet_count)
        self.formula_2_bullet_count.textChanged.connect(self.set_formula_2_bullet_count)
        self.formula_3_bullet_count.textChanged.connect(self.set_formula_3_bullet_count)
        self.formula_4_bullet_count.textChanged.connect(self.set_formula_4_bullet_count)
        self.select_formula_1.clicked.connect(lambda: self.set_formula_need_to_buy("1"))
        self.select_formula_2.clicked.connect(lambda: self.set_formula_need_to_buy("2"))
        self.select_formula_3.clicked.connect(lambda: self.set_formula_need_to_buy("3"))
        self.select_formula_4.clicked.connect(lambda: self.set_formula_need_to_buy("4"))
        self.start_btn.clicked.connect(lambda: self.bullet.start())
        self.stop_btn.clicked.connect(lambda: self.bullet.stop())
        self.feature_formula_ds.stateChanged.connect(lambda: self.set_feature_formula_ds(self.feature_formula_ds.isChecked()))
        self.feature_buy_direct.stateChanged.connect(lambda: self.set_feature_buy_direct(self.feature_buy_direct.isChecked()))
        self.feature_rolling.stateChanged.connect(lambda: self.set_feature_rolling(self.feature_rolling.isChecked()))
        self.direct_buy_min_bullet_price.textChanged.connect(self.set_direct_buy_min_bullet_price)
        self.direct_buy_max_bullet_price.textChanged.connect(self.set_direct_buy_max_bullet_price)
        self.expect_sell_price.textChanged.connect(self.set_expect_sell_price)

    def set_formula_max_price(self , value):
        """设置计划最大价格"""
        set_config("DEFAULT", "formula_max_price", value)

    def set_min_bullet_price(self , value):
        """设置子弹价格"""
        set_config("DEFAULT", "min_bullet_price", value)

    def set_max_bullet_price(self , value):
        """设置子弹价格"""
        set_config("DEFAULT", "max_bullet_price", value)

    def set_formula_1_bullet_count(self , value):
        """设置配装子弹数量"""
        set_config("DEFAULT", "formula_1_bullet_count", value)

    def set_formula_2_bullet_count(self , value):
        """设置配装子弹数量"""
        set_config("DEFAULT", "formula_2_bullet_count", value)

    def set_formula_3_bullet_count(self , value):
        """设置配装子弹数量"""
        set_config("DEFAULT", "formula_3_bullet_count", value)

    def set_formula_4_bullet_count(self , value):
        """设置配装子弹数量"""
        set_config("DEFAULT", "formula_4_bullet_count", value)

    def set_formula_need_to_buy(self , value):
        """设置需要购买的配装"""
        set_config("DEFAULT", "formula_need_to_buy", value)
        self.set_formula_need_to_buy_state(value)

    def set_formula_need_to_buy_state(self, formula_need_to_buy):
        if formula_need_to_buy == "1":
            self.select_formula_1.setChecked(True)
        elif formula_need_to_buy == "2":
            self.select_formula_2.setChecked(True)
        elif formula_need_to_buy == "3":
            self.select_formula_3.setChecked(True)
        elif formula_need_to_buy == "4":
            self.select_formula_4.setChecked(True)

        self.logger.info(f"当前需要购买的配装： {formula_need_to_buy}")

    def set_feature_formula_ds(self, value: bool):
        """设置档屎功能"""
        set_config("FEATURE", "formula_ds", "1" if value else "0")

    def set_feature_buy_direct(self, value: bool):
        """设置直接购买功能"""
        set_config("FEATURE", "direct_buy", "1" if value else "0")

    def set_feature_rolling(self, value: bool):
        """设置滚仓功能"""
        set_config("FEATURE", "rolling", "1" if value else "0")

    def set_direct_buy_min_bullet_price(self, value):
        """设置直接购买子弹价格"""
        set_config("DEFAULT", "direct_buy_min_bullet_price", value)

    def set_direct_buy_max_bullet_price(self, value):
        """设置直接购买子弹价格"""
        set_config("DEFAULT", "direct_buy_max_bullet_price", value)

    def set_expect_sell_price(self, value):
        """设置预期卖出价格"""
        set_config("DEFAULT", "expect_sell_price", value)

def __compute_absolute_position__(window_left, window_top, relative_position):
    """计算绝对位置"""
    x = window_left + relative_position[0]
    y = window_top + relative_position[1]
    width = relative_position[2]
    height = relative_position[3]
    return [x, y, width, height]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    configure_log_system()
    ex = WindowSelector()
    ex.show()
    app.exec()