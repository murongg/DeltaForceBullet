import pyautogui

def get_list_map_index(list_map, key, val):
    """获取列表中元素的索引"""
    index = [i for i, item in enumerate(list_map) if item[key] == val]
    return index[0] if index else -1

def take_screenshot(region, threshold=100):
    """截取指定区域的截图并二值化"""
    try:
        screenshot = pyautogui.screenshot(region=region)
        gray_image = screenshot.convert("L")  # 转换为灰度图像
        # binary_image = gray_image.point(lambda p: 255 if p > threshold else 0)
        # binary_image = Image.eval(binary_image, lambda x: 255 - x)
        screenshot.close()
        return gray_image
    except Exception as e:
        print(f"[错误] 截图失败: {str(e)}")
        return None
