#!/usr/bin/env python3
"""
Google Whisk AI 图像生成自动化 - 核心类 V2 (修复版)
修复：
1. 增加图片生成后的等待时间
2. 修复纵横比选择问题
"""

import json
import random
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Callable, Optional, List
from playwright.sync_api import sync_playwright, Download
import threading

class WhiskAutomationCoreV2:
    """Google Whisk AI 图像生成自动化核心类 V2"""
    
    # 支持的纵横比选项
    ASPECT_RATIOS = {
        '1:1': '正方形',
        '4:3': '标准横向', 
        '3:4': '标准纵向',
        '16:9': '宽屏横向',
        '9:16': '宽屏纵向'
    }
    
    def __init__(self, browser_id: str, save_directory: str, 
                 message_callback: Optional[Callable] = None,
                 progress_callback: Optional[Callable] = None,
                 use_enhanced_download: bool = True):
        self.browser_id = browser_id
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(exist_ok=True)
        self.use_enhanced_download = use_enhanced_download
        
        # 回调函数
        self.message_callback = message_callback or (lambda msg: print(msg))
        self.progress_callback = progress_callback or (lambda current, total: None)
        
        # 浏览器相关
        self.browser = None
        self.page = None
        self.playwright = None
        
        # 下载统计
        self.downloaded_count = 0
        
        # 线程安全锁
        self.lock = threading.Lock()
        
        # 页面元素选择器（基于新页面分析）
        self.selectors = {
            'textarea': 'textarea:visible',
            'download_button': 'button[aria-label="下载图片"]',
            'settings_button': 'button[aria-label*="设置面板"]',
            'aspect_ratio_dropdown': 'select:visible',
            'aspect_ratio_custom': '*:has-text("选择一种纵横"):visible'
        }
    
    def log(self, message: str):
        """发送日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_callback(f"[{timestamp}] {message}")
    
    def update_progress(self, current: int, total: int):
        """更新进度"""
        self.progress_callback(current, total)
    
    def get_bitbrowser_cdp(self) -> str:
        """调用比特浏览器 API 获取 CDP 端点"""
        try:
            api_url = f"http://127.0.0.1:54345/browser/open"
            payload = {"id": self.browser_id}
            
            self.log(f"正在连接比特浏览器，窗口ID: {self.browser_id}")
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data and 'ws' in data['data']:
                    ws_endpoint = data['data']['ws']
                    self.log(f"成功获取CDP端点: {ws_endpoint}")
                    return ws_endpoint
                else:
                    raise ValueError("无法从响应中获取WebSocket端点")
            else:
                raise Exception(f"比特浏览器API请求失败: {response.text}")
                
        except Exception as e:
            self.log(f"连接比特浏览器失败: {e}")
            raise
    
    def connect_browser(self):
        """连接到比特浏览器"""
        try:
            ws_endpoint = self.get_bitbrowser_cdp()
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(ws_endpoint)
            
            # 获取已有的页面或创建新页面
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                if pages:
                    self.page = pages[0]
                else:
                    self.page = context.new_page()
            else:
                raise Exception("浏览器没有可用的上下文")
                
            self.log("成功连接到浏览器")
            
            # 检查当前页面
            current_url = self.page.url
            self.log(f"当前页面: {current_url}")
            
            # 如果不在 Whisk 项目页面，尝试导航
            if "whisk/project" not in current_url and "whisk" not in current_url:
                self.log("不在 Whisk 页面，尝试导航...")
                self.page.goto("https://labs.google/fx/tools/whisk")
                time.sleep(3)
                
        except Exception as e:
            self.log(f"连接浏览器失败: {e}")
            raise
    
    def ensure_settings_panel_open(self):
        """确保设置面板打开"""
        try:
            # 检查设置面板是否可见
            settings_visible = self.page.query_selector('*:has-text("设置"):visible')
            
            if not settings_visible:
                # 打开设置面板
                settings_button = self.page.query_selector(self.selectors['settings_button'])
                if not settings_button:
                    # 尝试其他选择器
                    settings_button = self.page.query_selector('button:has-text("menu"):visible')
                
                if settings_button:
                    self.log("打开设置面板...")
                    settings_button.click()
                    time.sleep(2)
                else:
                    self.log("未找到设置按钮")
                    
        except Exception as e:
            self.log(f"打开设置面板失败: {e}")
    
    def select_aspect_ratio(self, aspect_ratio: str):
        """选择纵横比（新版页面）"""
        try:
            if aspect_ratio not in self.ASPECT_RATIOS:
                self.log(f"不支持的纵横比: {aspect_ratio}，使用默认设置")
                return
            
            self.log(f"选择纵横比: {aspect_ratio} ({self.ASPECT_RATIOS[aspect_ratio]})")
            
            # 新版页面：纵横比在底部工具栏
            # 1. 首先查找 aspect_ratio 按钮
            aspect_button = self.page.query_selector('button:has-text("aspect_ratio"):visible, button:has(i:has-text("aspect_ratio")):visible')
            
            if aspect_button:
                self.log("找到 aspect_ratio 按钮，点击打开纵横比面板")
                aspect_button.click()
                time.sleep(2)  # 等待面板展开
                
                # 2. 查找纵横比选项
                # 纵横比选项通常在彩色方块中显示
                ratio_buttons = self.page.query_selector_all('button:visible, div[role="button"]:visible')
                
                for button in ratio_buttons:
                    try:
                        text = button.text_content() or ""
                        # 匹配纵横比格式
                        if aspect_ratio in text:
                            self.log(f"找到 {aspect_ratio} 选项，点击...")
                            button.click()
                            self.log(f"✓ 成功选择纵横比: {aspect_ratio}")
                            time.sleep(2)  # 等待选择生效
                            
                            # 关闭纵横比面板（如果需要）
                            # 可以再次点击 aspect_ratio 按钮或点击其他地方
                            return
                    except:
                        pass
                
                # 如果没找到精确匹配，尝试其他方法
                self.log(f"未找到精确的 {aspect_ratio} 选项，尝试其他方法...")
                
                # 查找包含比例数字的元素
                for button in ratio_buttons:
                    try:
                        text = button.text_content() or ""
                        # 去除空格和特殊字符
                        clean_text = text.replace(" ", "").replace("\n", "")
                        if aspect_ratio.replace(":", "") in clean_text or aspect_ratio in clean_text:
                            self.log(f"找到匹配的选项: {text.strip()}")
                            button.click()
                            self.log(f"✓ 成功选择纵横比: {aspect_ratio}")
                            time.sleep(2)
                            return
                    except:
                        pass
                
                self.log(f"未找到 {aspect_ratio} 选项")
                
            else:
                # 尝试旧版方法（设置面板）
                self.log("未找到 aspect_ratio 按钮，尝试设置面板方法")
                self.ensure_settings_panel_open()
                time.sleep(1)
                
                # 查找下拉菜单
                dropdown = self.page.query_selector('select:visible')
                if dropdown:
                    try:
                        dropdown.select_option(value=aspect_ratio)
                        self.log(f"✓ 通过设置面板选择成功: {aspect_ratio}")
                        time.sleep(2)
                    except:
                        self.log("设置面板选择失败")
                        
        except Exception as e:
            self.log(f"选择纵横比失败: {e}")
    
    def input_prompt(self, prompt: str):
        """输入提示词"""
        try:
            self.log(f"输入提示词: {prompt[:50]}...")
            
            # 查找输入框
            textarea = self.page.query_selector(self.selectors['textarea'])
            
            if not textarea:
                raise Exception("未找到输入框")
            
            # 点击并清空
            textarea.click()
            time.sleep(0.5)
            
            # 清空现有内容
            textarea.select_text()
            textarea.type(prompt)
            
            # 验证输入
            value = textarea.input_value()
            if prompt in value:
                self.log("✓ 成功输入提示词")
            else:
                self.log("⚠ 提示词可能未完全输入")
                
        except Exception as e:
            self.log(f"输入提示词失败: {e}")
            raise
    
    def trigger_generation(self):
        """触发图片生成"""
        try:
            self.log("触发生成...")
            
            # 新版页面直接按回车即可
            self.page.keyboard.press('Enter')
            time.sleep(1)
            
            self.log("✓ 已触发生成")
            
        except Exception as e:
            self.log(f"触发生成失败: {e}")
            raise
    
    def wait_for_generation(self, timeout: int = 60):
        """等待图片生成完成（增加等待时间）"""
        try:
            self.log(f"等待生成完成 (最多 {timeout} 秒)...")
            
            start_time = time.time()
            initial_images = len(self.page.query_selector_all('img:visible'))
            
            while time.time() - start_time < timeout:
                time.sleep(3)  # 增加检查间隔
                
                # 检查新图片
                current_images = len(self.page.query_selector_all('img:visible'))
                if current_images > initial_images:
                    self.log(f"✓ 检测到新图片 (共 {current_images} 张)")
                    # 增加等待时间，确保图片完全生成
                    self.log("等待图片完全加载...")
                    time.sleep(7)  # 从2秒增加到7秒
                    return True
                
                # 检查下载按钮
                download_buttons = self.page.query_selector_all(self.selectors['download_button'] + ':visible')
                if download_buttons:
                    self.log(f"✓ 检测到下载按钮 ({len(download_buttons)} 个)")
                    # 额外等待确保所有元素加载完成
                    time.sleep(5)  # 新增5秒等待
                    return True
            
            self.log("⚠ 等待超时")
            return False
            
        except Exception as e:
            self.log(f"等待生成失败: {e}")
            return False
    
    def download_image(self, download_all: bool = True):
        """下载图片（默认下载所有图片）"""
        downloaded = 0
        
        try:
            if self.use_enhanced_download:
                self.log("使用增强版下载机制...")
                time.sleep(5)  # 增强版等待时间
            
            # 查找所有下载按钮
            download_buttons = self.page.query_selector_all(self.selectors['download_button'] + ':visible')
            
            if not download_buttons:
                self.log("未找到下载按钮")
                return 0
            
            self.log(f"找到 {len(download_buttons)} 个下载按钮")
            
            # Whisk现在一次生成2张图片，需要下载所有图片
            # 按位置排序，确保按顺序下载（左->右）
            button_positions = []
            for i, button in enumerate(download_buttons):
                try:
                    box = button.bounding_box()
                    if box:
                        button_positions.append({
                            'index': i,
                            'button': button,
                            'x': box['x']
                        })
                except:
                    pass
            
            # 按x坐标排序（从左到右）
            sorted_buttons = sorted(button_positions, key=lambda b: b['x'])
            
            # 下载所有图片
            for btn_info in sorted_buttons:
                try:
                    button = btn_info['button']
                    position = "左侧" if btn_info['index'] == 0 else "右侧"
                    
                    # 准备下载
                    with self.page.expect_download(timeout=30000) as download_info:
                        button.click()
                        download = download_info.value
                        
                        # 生成文件名
                        with self.lock:
                            self.downloaded_count += 1
                            count = self.downloaded_count
                        
                        filename = f"whisk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{count}_{position}.jpg"
                        save_path = self.save_directory / filename
                        
                        # 保存文件
                        download.save_as(save_path)
                        downloaded += 1
                        
                        self.log(f"✓ 下载成功 ({position}): {filename}")
                        
                    # 短暂延迟，避免下载冲突
                    time.sleep(1)
                        
                except Exception as e:
                    self.log(f"⚠ 下载失败: {e}")
                    
                    # 尝试截图保存
                    if self.use_enhanced_download:
                        try:
                            # 查找生成的大图片
                            images = self.page.query_selector_all('img:visible')
                            generated_images = []
                            
                            for img in images:
                                try:
                                    box = img.bounding_box()
                                    if box and box['width'] > 200 and box['height'] > 200:
                                        generated_images.append({
                                            'element': img,
                                            'x': box['x']
                                        })
                                except:
                                    pass
                            
                            # 按x坐标排序
                            sorted_images = sorted(generated_images, key=lambda img: img['x'])
                            
                            # 保存对应位置的图片
                            if btn_info['index'] < len(sorted_images):
                                img_element = sorted_images[btn_info['index']]['element']
                                
                                with self.lock:
                                    self.downloaded_count += 1
                                    count = self.downloaded_count
                                
                                position = "左侧" if btn_info['index'] == 0 else "右侧"
                                filename = f"whisk_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{count}_{position}.png"
                                save_path = self.save_directory / filename
                                
                                img_element.screenshot(path=save_path)
                                downloaded += 1
                                
                                self.log(f"✓ 截图保存 ({position}): {filename}")
                        except:
                            pass
            
            return downloaded
            
        except Exception as e:
            self.log(f"下载过程出错: {e}")
            return downloaded
    
    def generate_images(self, prompt: str, count: int, aspect_ratio: str = "1:1", 
                       min_delay: int = 5, max_delay: int = 8):
        """生成多张图片的主流程"""
        try:
            self.log(f"开始生成任务: {count} 次生成, 比例 {aspect_ratio} (每次生成2张图片)")
            
            # 选择纵横比（每次任务开始时设置一次）
            if aspect_ratio != "1:1":  # 如果不是默认比例
                self.select_aspect_ratio(aspect_ratio)
                time.sleep(2)  # 等待设置生效
            
            # 生成图片
            for i in range(count):
                self.log(f"\n--- 第 {i+1}/{count} 次生成 ---")
                self.update_progress(i, count)
                
                # 输入提示词
                self.input_prompt(prompt)
                
                # 触发生成
                self.trigger_generation()
                
                # 等待生成
                if self.wait_for_generation():
                    # 下载图片（Whisk现在一次生成2张）
                    downloaded = self.download_image()
                    if downloaded > 0:
                        self.log(f"✓ 第 {i+1} 次生成完成，下载了 {downloaded} 张图片")
                    else:
                        self.log(f"⚠ 第 {i+1} 次生成下载失败")
                else:
                    self.log(f"⚠ 第 {i+1} 次生成超时")
                
                # 延迟
                if i < count - 1:
                    delay = random.randint(min_delay, max_delay)
                    self.log(f"等待 {delay} 秒...")
                    time.sleep(delay)
            
            self.update_progress(count, count)
            self.log(f"\n✅ 任务完成！共下载 {self.downloaded_count} 张图片")
            self.log(f"保存位置: {self.save_directory}")
            
        except Exception as e:
            self.log(f"❌ 生成过程出错: {e}")
            raise
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.log("资源清理完成")
        except Exception as e:
            self.log(f"清理资源时出错: {e}")
    
    def run(self, prompt: str, count: int, aspect_ratio: str = "1:1",
            min_delay: int = 5, max_delay: int = 8):
        """运行完整的自动化流程"""
        try:
            # 连接浏览器
            self.connect_browser()
            
            # 生成图片
            self.generate_images(prompt, count, aspect_ratio, min_delay, max_delay)
            
        except Exception as e:
            self.log(f"运行失败: {e}")
            raise
        finally:
            # 清理资源
            self.cleanup()