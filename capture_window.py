"""捕获WhiskAI窗口截图"""
import pyautogui
import pygetwindow as gw
import time

try:
    # 查找WhiskAI窗口
    windows = gw.getWindowsWithTitle('WhiskAI')

    if not windows:
        print("未找到WhiskAI窗口，尝试查找所有窗口...")
        all_windows = gw.getAllTitles()
        whisk_windows = [w for w in all_windows if 'Whisk' in w or 'whisk' in w]
        print(f"找到的Whisk相关窗口: {whisk_windows}")

        if whisk_windows:
            windows = [gw.getWindowsWithTitle(whisk_windows[0])[0]]

    if windows:
        window = windows[0]
        print(f"找到窗口: {window.title}")

        # 激活窗口
        window.activate()
        time.sleep(0.5)

        # 获取窗口位置和大小
        left, top, width, height = window.left, window.top, window.width, window.height
        print(f"窗口位置: ({left}, {top}), 大小: {width}x{height}")

        # 截取窗口区域
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot.save('whisk_window.png')
        print("截图已保存: whisk_window.png")
    else:
        # 如果找不到窗口，就截取整个屏幕
        print("未找到WhiskAI窗口，截取整个屏幕")
        screenshot = pyautogui.screenshot()
        screenshot.save('whisk_window.png')
        print("截图已保存: whisk_window.png")

except Exception as e:
    print(f"截图失败: {e}")
    # 备用方案：截取整个屏幕
    import pyautogui
    screenshot = pyautogui.screenshot()
    screenshot.save('whisk_window.png')
    print("使用备用方案截图: whisk_window.png")
