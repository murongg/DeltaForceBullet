import os
import threading
import time
import traceback
from typing import Optional, List, Callable

import numpy as np
import pyautogui
import win32gui
from PyQt5.QtCore import QObject

os.environ["TQDM_DISABLE"] = "1"

from paddleocr import PaddleOCR
from pygetwindow import Win32Window

from config import get_config
from utils import take_screenshot

default_balance_text_position = [1050,210,100,20] # [x, y, width, height]
default_balance_position = [1110,60,100,20]
default_rou_buy_btn_position = [990,600,200,40]
default_gold_buy_btn_position = [990,610,200,40]
default_price_position = [200,140,200,30]
default_first_formula_position = [60,170,150,40]
default_formula_space_size = 10
default_formula_buy_btn_position = [1030,592,200,40]
default_formula_buy_btn_price_position = [1107,603,76,16]
default_storehouse_btn_position = [180, 52, 85, 30]
default_first_group_bullets_position = [454,274,46,46]
default_sell_btn_position = [550,270,115,19]
default_publish_to_trade_btn_position = [880,485,120,26]
default_publish_to_trade_modify_price_position = [917,459,1,1]
default_publish_btn_position = [780,510,200,40]
default_add_btn_on_trade_card_position = [990,392,25,25]
default_price_change_position = [278, 186,140,30]
default_into_plan_btn_position = [160, 720, 65, 25]
default_mail_icon_btn_position = [1158,60,18,18]
default_collect_all_btn_position = [68, 656, 128, 30]
default_mail_trade_btn_position = [260, 65, 87, 32]
default_start_game_btn_position = [87, 53, 85, 30]
default_sell_count_position = [795,370,110,20]
default_publish_progress_bar_position = [745, 401, 193, 8]
default_sale_space_count_position = [980,370,80,20] # 售位位置

def __compute_absolute_position__(window_left, window_top, relative_position):
    """计算绝对位置"""
    x = window_left + relative_position[0]
    y = window_top + relative_position[1]
    width = relative_position[2]
    height = relative_position[3]
    return [x, y, width, height]


class OCRProcessor:
    def __init__(self):
        self._ch_ocr: Optional[PaddleOCR] = None
        self._en_ocr: Optional[PaddleOCR] = None

    @property
    def chinese_ocr(self) -> PaddleOCR:
        if not self._ch_ocr:
            self._ch_ocr = PaddleOCR(use_angle_cls=True, use_gpu=True, lang='ch')
        return self._ch_ocr

    @property
    def english_ocr(self) -> PaddleOCR:
        if not self._en_ocr:
            self._en_ocr = PaddleOCR(use_angle_cls=True, use_gpu=True, lang='en')
        return self._en_ocr

    def unregister(self):
        """注销OCR实例"""
        if self._ch_ocr:
            self._ch_ocr = None
        if self._en_ocr:
            self._en_ocr = None

    def extract_numeric_value(self, region: List[int]) -> Optional[int]:
        try:
            screenshot = take_screenshot(region, 100)
            # screenshot.save('./images/screenshot.png')
            image = np.array(screenshot)
            result = self._recognize_with_fallback(image)
            return int(''.join(filter(str.isdigit, result))) if result else None
        except Exception as e:
            traceback.print_exc()
            return None

    def get_text_by_region(self, region: List[int]) -> str:
        try:
            screenshot = take_screenshot(region, 100)
            # screenshot.save('./images/screenshot.png')
            image = np.array(screenshot)
            result = self._recognize_with_fallback(image)
            return result if result else ""
        except Exception as e:
            traceback.print_exc()
            return ""

    def _recognize_with_fallback(self, image: np.ndarray) -> str:
        result = self.english_ocr.ocr(image, cls=True)
        if not result or not result[0]:
            result = self.chinese_ocr.ocr(image, cls=True)
        if not result or not result[0]:
            return ""
        return result[0][0][1][0] if result else ""


class Bullet(QObject):
    """
    window A: 检测端，负责交易行页面低价子弹检测
    window B: 购买端，负责配装页面和仓库的滚仓买卖
    """
    _stop_event = threading.Event()
    _thread:threading.Thread = None
    max_bullet_price = 4100
    min_bullet_price = 2000
    formula_max_price = 4500
    formula_1_bullet_count = 1200
    formula_2_bullet_count = 1200
    formula_3_bullet_count = 1200
    formula_4_bullet_count = 1200
    formula_need_to_buy = 1
    formula_ds = False
    direct_buy = False
    rolling = False
    expect_sell_price = 0

    remaining_count = 1 # 默认设置为1，保证程序正常执行

    ocr_processor = OCRProcessor()

    window_a_info = {}
    window_b_info = {}

    def __init__(self, parent):
        super().__init__()
        self.direct_buy_max_bullet_price = None
        self.direct_buy_min_bullet_price = None
        self.parent = parent

    def refresh_config(self):
        """刷新配置"""
        formula_max_price = get_config("DEFAULT", "formula_max_price")
        max_bullet_price = get_config("DEFAULT", "max_bullet_price")
        min_bullet_price = get_config("DEFAULT", "min_bullet_price")
        formula_1_bullet_count = get_config("DEFAULT", "formula_1_bullet_count")
        formula_2_bullet_count = get_config("DEFAULT", "formula_2_bullet_count")
        formula_3_bullet_count = get_config("DEFAULT", "formula_3_bullet_count")
        formula_4_bullet_count = get_config("DEFAULT", "formula_4_bullet_count")
        formula_need_to_buy = get_config("DEFAULT", "formula_need_to_buy")
        formula_ds = get_config("FEATURE", "formula_ds")
        direct_buy = get_config("FEATURE", "direct_buy")
        rolling = get_config("FEATURE", "rolling")
        self.formula_max_price = int(formula_max_price)
        self.max_bullet_price = int(max_bullet_price)
        self.min_bullet_price = int(min_bullet_price)
        self.formula_1_bullet_count = int(formula_1_bullet_count)
        self.formula_2_bullet_count = int(formula_2_bullet_count)
        self.formula_3_bullet_count = int(formula_3_bullet_count)
        self.formula_4_bullet_count = int(formula_4_bullet_count)
        self.formula_need_to_buy = int(formula_need_to_buy)
        self.formula_ds = formula_ds == "1"
        self.direct_buy = direct_buy == "1"
        self.rolling = rolling == "1"
        self.direct_buy_min_bullet_price = int(get_config("DEFAULT", "direct_buy_min_bullet_price"))
        self.direct_buy_max_bullet_price = int(get_config("DEFAULT", "direct_buy_max_bullet_price"))
        self.expect_sell_price = int(get_config("DEFAULT", "expect_sell_price"))
        self.__computed_window_a_buy_btn_position__()

        if self.window_a_info.get("hwnd") is not None:
            self.set_window_a_info(self.window_a_info.get("hwnd"))

        if self.window_b_info.get("hwnd") is not None:
            self.set_window_b_info(self.window_b_info.get("hwnd"))

    def __computed_window_a_buy_btn_position__(self):
        """计算检测端窗口的购买按钮位置"""
        if self.window_a_info.get("self") is None:
            self.parent.logger.error("检测端窗口信息未设置，无法计算购买按钮位置")
            return
        [left, top, _, _] = self.window_a_info["self"]
        self.window_a_info['buy_btn_position'] = __compute_absolute_position__(left, top, default_rou_buy_btn_position)

    def set_window_a_info(self, hwnd: int):
        """设置检测端窗口的位置信息"""
        title = win32gui.GetWindowText(hwnd)
        cls_name = win32gui.GetClassName(hwnd)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        self.window_a_info["self"] = [left, top, width, height]
        self.window_a_info["hwnd"] = hwnd
        self.window_a_info["title"] = title
        self.window_a_info["cls_name"] = cls_name
        self.window_a_info["width"] = width
        self.window_a_info["height"] = height
        self.window_a_info["balance_text_position"] = __compute_absolute_position__(left,top,default_balance_text_position)
        self.window_a_info["balance_position"] = __compute_absolute_position__(left,top,default_balance_position)
        self.window_a_info["price_text_position"] = __compute_absolute_position__(left,top,default_price_position)
        self.__computed_window_a_buy_btn_position__()

        return self.window_a_info

    def set_window_b_info(self, hwnd: int):
        """设置购买端窗口的位置信息"""
        title = win32gui.GetWindowText(hwnd)
        cls_name = win32gui.GetClassName(hwnd)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        self.window_b_info["self"] = [left, top, width, height]
        self.window_b_info["hwnd"] = hwnd
        self.window_b_info["title"] = title
        self.window_b_info["cls_name"] = cls_name
        self.window_b_info["width"] = width
        self.window_b_info["height"] = height
        self.window_b_info["first_formula_position"] = __compute_absolute_position__(left, top, default_first_formula_position)
        self.window_b_info["formula_space_size"] = default_formula_space_size
        self.window_b_info["formula_buy_btn_position"] = __compute_absolute_position__(left, top, default_formula_buy_btn_position)
        self.window_b_info["formula_buy_btn_price_position"] = __compute_absolute_position__(left, top, default_formula_buy_btn_price_position)
        self.window_b_info["first_group_bullets_position"] = __compute_absolute_position__(left, top, default_first_group_bullets_position)
        self.window_b_info["storehouse_btn_position"] = __compute_absolute_position__(left, top, default_storehouse_btn_position)
        self.window_b_info["sell_btn_position"] = __compute_absolute_position__(left, top, default_sell_btn_position)
        self.window_b_info["publish_to_trade_btn_position"] = __compute_absolute_position__(left, top, default_publish_to_trade_btn_position)
        self.window_b_info["publish_to_trade_modify_price_position"] = __compute_absolute_position__(left, top, default_publish_to_trade_modify_price_position)
        self.window_b_info["publish_btn_position"] = __compute_absolute_position__(left, top, default_publish_btn_position)
        self.window_b_info["add_btn_on_trade_card_position"] = __compute_absolute_position__(left, top, default_add_btn_on_trade_card_position)
        self.window_b_info["price_change_position"] = __compute_absolute_position__(left, top, default_price_change_position)
        self.window_b_info["into_plan_btn_position"] = __compute_absolute_position__(left, top, default_into_plan_btn_position)
        self.window_b_info["mail_icon_btn_position"] = __compute_absolute_position__(left, top, default_mail_icon_btn_position)
        self.window_b_info["collect_all_btn_position"] = __compute_absolute_position__(left, top, default_collect_all_btn_position)
        self.window_b_info["mail_trade_btn_position"] = __compute_absolute_position__(left, top, default_mail_trade_btn_position)
        self.window_b_info["start_game_btn_position"] = __compute_absolute_position__(left, top, default_start_game_btn_position)
        self.window_b_info["sell_count_position"] = __compute_absolute_position__(left, top, default_sell_count_position)
        self.window_b_info["publish_progress_bar_position"] = __compute_absolute_position__(left, top, default_publish_progress_bar_position)
        self.window_b_info["sale_space_count_position"] = __compute_absolute_position__(left, top, default_sale_space_count_position)
        return self.window_b_info

    def set_window_a_active(self):
        """设置检测端窗口为活动窗口"""
        if self.window_a_info["hwnd"] is not None:
            self.parent.logger.info("设置检测端窗口为活动窗口")
            win = Win32Window(self.window_a_info["hwnd"])
            win.activate()

        else:
            self.parent.logger.error("检测端窗口句柄为空，无法设置为活动窗口")
            return

    def set_window_b_active(self):
        """设置购买端窗口为活动窗口"""
        if self.window_b_info["hwnd"] is not None:
            self.parent.logger.info("设置购买端窗口为活动窗口")
            win = Win32Window(self.window_b_info["hwnd"])
            win.activate()
        else:
            self.parent.logger.error("购买端窗口句柄为空，无法设置为活动窗口")
            return

    def move_to_balance_position(self):
        """移动鼠标到余额位置"""
        [left, top, width, height] = self.window_a_info["balance_position"]
        x, y = WindowOperator.compute_center_pos(left, top, width, height)
        pyautogui.moveTo(x, y)

    def get_balance(self):
        # 获取余额文本
        balance_text_region = self.window_a_info["balance_text_position"]
        try:
            price = self.ocr_processor.extract_numeric_value(balance_text_region)
            return price
        except ValueError:
            self.parent.logger.warning("无法解析价格")
            return None

    def click_buy_btn(self):
        """点击购买按钮"""
        self.click_btn(self.window_a_info["buy_btn_position"])

    def window_a_task(self):
       """运行检测端窗口的操作"""
       # 获取检测端窗口的位置信息
       hwnd = self.window_a_info["hwnd"]
       if hwnd is None:
           return
       # 设置检测端窗口为活动窗口
       self.set_window_a_active()

       is_buy = False
       self.move_to_balance_position()
       last_balance = self.get_balance()
       if last_balance is None:
           last_balance = 0
       while not self._stop_event.is_set():
           self.parent.logger.info(f"上次余额: {last_balance}")
           self.click_buy_btn()
           self.move_to_balance_position()
           current_balance = self.get_balance()
           if current_balance is None:
               self.parent.logger.info("获取current balance失败")
               continue
           self.parent.logger.info(f"当前余额: {current_balance}")
           single_bullet_price = last_balance - current_balance
           self.parent.logger.info(f"单发子弹价格: {single_bullet_price}")
           last_balance = current_balance
           if self.max_bullet_price >= single_bullet_price >= self.min_bullet_price:
               self.parent.logger.info("GO")
               is_buy = self.switch_window_b_to_buy()
               break

       # time.sleep(1)
       if not is_buy and not self._stop_event.is_set():
           self.click_into_plan_btn()
           # 继续检测
           self.window_b_task()

    def window_b_task(self):
        """运行购买端窗口的操作"""
        # 获取购买端窗口的位置信息
        hwnd = self.window_b_info["hwnd"]
        if hwnd is None:
            return

        # 设置购买端窗口为活动窗口
        self.set_window_b_active()

        # 切换formula选项卡，共四个
        self.check_formula_page_bullet_price()

    def pre_check(self):
        """预检查"""
        # 检查检测端窗口和购买端窗口是否存在
        if self.window_a_info.get("hwnd") is None:
            self.parent.logger.error("检测端窗口不存在，请检查")
            return False
        if self.window_b_info.get("hwnd") is None:
            self.parent.logger.error("购买端窗口不存在，请检查")
            return False

        return True

    def run_task(self):
        try:
            if self.formula_ds or self.direct_buy:
                self.window_b_task()
            else:
                self.window_a_task()
        except Exception as e:
            s = traceback.format_exc()
            self.parent.logger.error(f"发生异常: {str(e)}")
            self.parent.logger.error("详细错误信息: %s", s)
            # raise e

    def start(self):
        if self._thread and self._thread.is_alive():
            self.parent.logger.info("购买线程已在运行中")
            return
        if not self.pre_check():
            return
        self.refresh_config()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.run_task, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                self.parent.logger.warning("购买线程未能正常停止，即将强制回收")
            self._thread = None
        self.ocr_processor.unregister()
        self.parent.logger.info("已停止购买")

    def get_formula_buy_btn_position_price(self):
        """获取购买按钮的文本"""
        formula_buy_btn_region = self.window_b_info["formula_buy_btn_price_position"]
        try:
            price = self.ocr_processor.extract_numeric_value(formula_buy_btn_region)
            return price
        except ValueError:
            return None

    def get_publish_to_trade_btn_text(self):
        region = self.window_b_info["publish_to_trade_btn_position"]
        text = self.ocr_processor.get_text_by_region(region)
        return text

    def check_formula_page_bullet_price(self):
        bullet_count_list = [self.formula_1_bullet_count, self.formula_2_bullet_count, self.formula_3_bullet_count, self.formula_4_bullet_count]
        is_break = False
        direct_buy_success = False

        while not self._stop_event.is_set():
            if is_break:
                break

            for i in range(3):
                self.switch_formula_panel(i + 1)
                # time.sleep(0.2)
                total_price = self.get_formula_buy_btn_position_price()
                if total_price is None:
                    self.parent.logger.info("无法解析价格")
                    continue
                count = bullet_count_list[i]
                price = total_price / count
                self.parent.logger.info(f"当前计划{i + 1}的单发子弹价格: {price}")
                self.parent.logger.info(f"当前计划{i + 1}的总价格: {total_price}")
                self.parent.logger.info(f"当前计划{i + 1}的子弹数量: {count}")
                # if self.direct_buy:
                #     self.parent.logger.info(f"当前已启动直接购买，尝试直接购买")
                #     if self.direct_buy_max_bullet_price >= price >= self.direct_buy_min_bullet_price:
                #         self.parent.logger.info(f"检测到最低价格正在尝试购买")
                #         direct_buy_success = self.direct_buy_bullet()
                #         if direct_buy_success:
                #             self.parent.logger.info(f"直接购买成功，当前价格: {price}")
                #             self.sell_bullet_in_storehouse()
                #             is_break = not self.rolling
                #             break
                #     else:
                #         self.parent.logger.info(f"当前价格不在范围内，无法直接购买")
                if self.formula_ds:
                    if self.formula_max_price >= price >= self.min_bullet_price:
                        self.parent.logger.info(f"检测到档屎价格，正在切换检测端进行检测")
                        is_break = True
                        break

        # 切换到检测端检测子弹价格
        if self.formula_ds and not self._stop_event.is_set():
            self.window_a_task()

    def direct_buy_bullet(self):
        # self.switch_formula_panel(self.formula_need_to_buy)
        if self.window_b_buy():
            return True
        # 点击进入计划按钮
        self.click_into_plan_btn()
        time.sleep(1)
        return False

    def window_b_buy(self):
        # self.switch_formula_panel(4)
        self.buy_from_formula_page()
        time.sleep(1)
        # 检测是否有价格变动窗口
        if self.has_price_change_card():
            self.parent.logger.info("检测到价格变动窗口")
            # 检测是否有价格变动窗口
            time.sleep(1)
            WindowOperator.press("esc")
            return False
        # 执行出售逻辑
        self.sell_bullet_in_storehouse()
        return True

    def switch_window_b_to_buy(self):
        """切换到购买端"""
        # 设置购买端窗口为活动窗口
        self.set_window_b_active()
        # 切换到指定panel
        self.switch_formula_panel(self.formula_need_to_buy)
        return self.window_b_buy()

    def has_price_change_card(self):
        """检查是否有价格变动窗口"""
        position = self.window_b_info["price_change_position"]
        text = self.ocr_processor.get_text_by_region(position)
        if text is None:
            self.parent.logger.info("未识别到价格变动窗口")
            return False
        return "价格变动提醒" in text

    def click_into_plan_btn(self):
        """点击进入计划按钮"""
        self.click_btn(self.window_b_info["into_plan_btn_position"])

    def switch_formula_panel(self, num):
        self.click_btn(self.__compute_formula_position__(num))

    def buy_from_formula_page(self):
        self.click_btn(self.window_b_info["formula_buy_btn_position"])

    def sell_bullet_in_storehouse(self):
        """在仓库窗口出售子弹"""
        if not self.rolling:
            self.parent.logger.info("未开启滚仓模式，跳过出售子弹")
            return
        self.remaining_count = 1
        self.parent.logger.info("正在执行出售逻辑")
        while not self._stop_event.is_set() :
            if self.remaining_count <= 0:
                self.parent.logger.info("本次子弹售卖完成，剩余子弹数量为0")
                break
            # 进入配装页面设置配装
            self.to_formula_page()
            time.sleep(0.5)
            self.switch_formula_panel(4)
            self.buy_from_formula_page()
            time.sleep(1)
            # 获取仓库按钮的位置，并且定位到
            self.click_btn(self.window_b_info["storehouse_btn_position"])
            time.sleep(0.5)
            self.click_btn(self.window_b_info["first_group_bullets_position"])
            time.sleep(0.5)
            self.click_btn(self.window_b_info["sell_btn_position"])
            time.sleep(0.5)
            publish_to_trade_btn_text = self.get_publish_to_trade_btn_text()
            if publish_to_trade_btn_text is None or "上架" not in publish_to_trade_btn_text:
                self.parent.logger.info("未识别到上架按钮，结束本次上架交易行操作")
                return

            self.parent.logger.info(f"上架按钮文本: {publish_to_trade_btn_text}")
            self.click_btn(self.window_b_info["publish_to_trade_btn_position"])
            time.sleep(0.3)

            # 选择出售子弹进度条
            progress_success = self.select_need_to_sell_bullet_count()
            if not progress_success:
                self.parent.logger.info("未选择出售子弹进度条，结束本次上架交易行操作")
                break
            # 获取剩余子弹数量
            remaining, sell, all = self.get_remaining_bullet_count()
            self.remaining_count = remaining
            # 修改价格
            self.click_btn(self.window_b_info["publish_to_trade_modify_price_position"])
            for i in range(5):
                WindowOperator.press("backspace")

            for i in str(self.expect_sell_price):
                WindowOperator.press(i)

            # # 点击上架按钮
            self.click_btn(self.window_b_info["publish_btn_position"])

            time.sleep(3)
            self.to_mail_get_money()
            time.sleep(0.5)

        # 进入配装页面继续执行购买
        self.parent.logger.info("继续执行购买")
        self.to_formula_page()
        time.sleep(0.5)

    def get_remaining_bullet_count(self):
        """获取剩余子弹数量"""
        [x,y,w,h] = self.window_b_info["sell_count_position"]
        WindowOperator.move(x,y)
        text = self.ocr_processor.get_text_by_region([x,y,w,h])
        if text is None:
            self.parent.logger.info("未识别到剩余子弹数量")
            return 0,0,0
        # 以 / 分割
        text = text.split("/")
        if len(text) != 2:
            self.parent.logger.info("剩余子弹数量格式错误")
            return 0,0,0
        sell_count = int(text[0])
        all_count = int(text[1])
        remaining = all_count - sell_count
        if remaining < 0:
            self.parent.logger.info("剩余子弹数量小于0")
            return 0,0,0
        self.parent.logger.info(f"当前卖出子弹数量: {sell_count}，总数量: {all_count}，剩余数量: {remaining}")
        return remaining, sell_count, all_count

    def get_sale_space_count(self):
        """获取剩余售位数量"""
        [x,y,w,h] = self.window_b_info["sale_space_count_position"]
        WindowOperator.move(x,y)
        text = self.ocr_processor.get_text_by_region([x,y,w,h])
        if text is None:
            self.parent.logger.info("未识别到剩余售位数量")
            return 0
        # 以 / 分割
        text = text.split("/")
        if len(text) != 2:
            self.parent.logger.info("剩余售位数量格式错误")
            return 0
        sell_count = int(text[0])
        all_count = int(text[1])
        remaining = all_count - sell_count + 1
        if remaining < 0:
            self.parent.logger.info("剩余售位数量小于0")
            return 0
        self.parent.logger.info(f"当前售位数量: {sell_count}，总数量: {all_count}，剩余数量: {remaining}")
        return remaining, sell_count, all_count

    def click_btn(self, pos: List[int]):
        """点击指定位置"""
        [left, top, width, height] = pos
        x, y = WindowOperator.compute_center_pos(left, top, width, height)
        WindowOperator.click(x, y)

    def to_mail_get_money(self):
        # 进入邮件
        self.click_btn(self.window_b_info["mail_icon_btn_position"])
        # 点击交易行按钮
        self.click_btn(self.window_b_info["mail_trade_btn_position"])
        # 点击全部领取
        self.click_btn(self.window_b_info["collect_all_btn_position"])
        time.sleep(3)
        WindowOperator.press("esc")
        time.sleep(1)
        WindowOperator.press("esc")

    def to_formula_page(self):
        """切换到配装页面"""
        # 点击开始游戏按钮
        self.click_btn(self.window_b_info["start_game_btn_position"])
        time.sleep(1)
        self.click_into_plan_btn()

    def select_need_to_sell_bullet_count(self):
        """根据剩余售位和当前子弹数量选择需要出售的子弹数量"""
        # 获取剩余子弹数量
        bullet_remaining_count, bullet_sell_count, bullet_all_count = self.get_remaining_bullet_count()
        if bullet_remaining_count <= 0:
            self.parent.logger.info("剩余子弹数量为0，无法出售")
            return False
        # 获取当前子弹数量
        sale_remaining_count,  sale_sell_count, sale_all_count =  self.get_sale_space_count()
        if sale_remaining_count <= 0:
            self.parent.logger.info("剩余售位数量为0，无法出售")
            return False
        # 每个售位200发子弹
        can_sale_count = sale_remaining_count * 200
        # progress bar 百分比
        if can_sale_count >= bullet_all_count:
            progress_bar_percent = 1
        else:
            progress_bar_percent = (can_sale_count / bullet_all_count)

        self.parent.logger.info(f"当前剩余子弹数量: {bullet_remaining_count}，当前售位数量: {sale_remaining_count}，进度条百分比: {progress_bar_percent}")
        # 计算Progress bar 位置
        [left,top,width,height] = self.window_b_info["publish_progress_bar_position"]
        x = left + (width * progress_bar_percent )
        # 对x保留两位小数处理
        x = round(x, 2)
        y = top + height // 2
        # 点击进度条
        WindowOperator.click(x, y)
        return True

    def __compute_formula_position__(self, formula_num: int):
        """计算计划位置"""
        [left, top, width, height] = self.window_b_info["first_formula_position"]
        x = left
        space = (self.window_b_info["formula_space_size"] * (formula_num - 1))
        y = top + height * formula_num + space
        return [x, y, width, height]

class WindowOperator:
    @staticmethod
    def click(x,y):
        """点击指定位置"""
        pyautogui.moveTo(x, y)
        pyautogui.click(x, y)

    @staticmethod
    def move(x, y):
        """移动鼠标到指定位置"""
        pyautogui.moveTo(x, y)

    @staticmethod
    def compute_center_pos(x, y, w, h):
        """计算中心点"""
        return x + w // 2, y + h // 2

    @staticmethod
    def press(key):
        """按下指定键"""
        pyautogui.press(key)

