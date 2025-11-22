"""截图工具 - 捕获WhiskAI窗口"""
import pyautogui
import time

# 等待一秒确保窗口在前台
time.sleep(1)

# 截取整个屏幕
screenshot = pyautogui.screenshot()

# 保存截图
screenshot.save('whisk_v3_screenshot.png')
print("截图已保存: whisk_v3_screenshot.png")
