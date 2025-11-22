#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        self.total_images_expected = 0
        
        # 任务控制
        self.should_stop = False
        self.is_running = False
        
        # 线程安全锁
        self.lock = threading.Lock()
        
        # 去重机制：记录已下载的图片URL
        self.downloaded_urls = set()
        # 记录生成前的图片URL，用于识别新生成的图片
        self.pre_generation_urls = set()
        
        # 页面元素选择器（基于新页面分析）
        self.selectors = {
            'textarea': 'textarea:visible',
            'download_button': 'button[aria-label="下载图片"]',
            'settings_button': 'button[aria-label*="设置面板"]',
            'aspect_ratio_dropdown': 'select:visible',
            'aspect_ratio_custom': '*:has-text("选择一种纵横"):visible'
        }
    
    def stop_task(self):
        """停止当前任务"""
        with self.lock:
            self.should_stop = True
        self.log("收到停止任务请求")
    
    def is_task_stopped(self) -> bool:
        """检查任务是否应该停止"""
        with self.lock:
            return self.should_stop
    
    def reset_task_state(self):
        """重置任务状态"""
        with self.lock:
            self.should_stop = False
            self.is_running = False
            self.downloaded_count = 0
            self.total_images_expected = 0
            # 清空URL去重集合，确保任务间完全隔离
            self.downloaded_urls.clear()
            self.pre_generation_urls.clear()
    
    def log(self, message: str):
        """发送日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_callback(f"[{timestamp}] {message}")
    
    def update_progress(self, current: int, total: int, progress_type: str = 'generation'):
        """更新进度"""
        self.progress_callback(current, total, progress_type)
    
    def update_download_progress(self):
        """更新下载进度"""
        with self.lock:
            # 使用相对计数：本任务实际下载数
            downloaded = self.downloaded_count - getattr(self, 'task_start_count', 0)
            expected = self.total_images_expected
        
        if expected > 0:
            # 发送下载进度更新
            self.update_progress(downloaded, expected, 'download')
    
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
                            self.log(f"[OK] 成功选择纵横比: {aspect_ratio}")
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
                            self.log(f"[OK] 成功选择纵横比: {aspect_ratio}")
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
                        self.log(f"[OK] 通过设置面板选择成功: {aspect_ratio}")
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
                self.log("[OK] 成功输入提示词")
            else:
                self.log("[WARNING] 提示词可能未完全输入")
                
        except Exception as e:
            self.log(f"输入提示词失败: {e}")
            raise
    
    def record_current_images(self):
        """记录当前页面的图片URL，用于识别新生成的图片"""
        try:
            self.pre_generation_urls.clear()
            images = self.page.query_selector_all('img:visible')
            
            for img in images:
                try:
                    box = img.bounding_box()
                    if box and box['width'] > 200 and box['height'] > 200:
                        # 获取图片的src属性
                        src = img.get_attribute('src')
                        if src:
                            self.pre_generation_urls.add(src)
                except:
                    pass
            
            self.log(f"记录了 {len(self.pre_generation_urls)} 张现有图片")
            
        except Exception as e:
            self.log(f"记录图片失败: {e}")
    
    def trigger_generation(self):
        """触发图片生成"""
        try:
            # 在生成前记录当前的图片
            self.record_current_images()
            
            self.log("触发生成...")
            
            # 新版页面直接按回车即可
            self.page.keyboard.press('Enter')
            time.sleep(1)
            
            self.log("[OK] 已触发生成")
            
        except Exception as e:
            self.log(f"触发生成失败: {e}")
            raise
    
    def wait_for_generation(self, timeout: int = 60):
        """等待图片生成完成（改进版：检测URL变化）"""
        try:
            self.log(f"等待生成完成 (最多 {timeout} 秒)...")
            
            start_time = time.time()
            
            # 获取初始的图片URL集合（不只是数量）
            initial_urls = set()
            initial_count = 0
            images = self.page.query_selector_all('img:visible')
            for img in images:
                try:
                    box = img.bounding_box()
                    if box and box['width'] > 200 and box['height'] > 200:
                        src = img.get_attribute('src')
                        if src:
                            initial_urls.add(src)
                            initial_count += 1
                except:
                    pass
            
            self.log(f"初始状态: {initial_count} 张大图片")
            
            # 使用更短的检查间隔和多种检测方式
            check_interval = 1.5  # 缩短检查间隔
            last_log_time = time.time()
            
            while time.time() - start_time < timeout:
                time.sleep(check_interval)
                
                # 方法1：检查URL是否有变化（最可靠）
                current_urls = set()
                current_count = 0
                images = self.page.query_selector_all('img:visible')
                for img in images:
                    try:
                        box = img.bounding_box()
                        if box and box['width'] > 200 and box['height'] > 200:
                            src = img.get_attribute('src')
                            if src:
                                current_urls.add(src)
                                current_count += 1
                    except:
                        pass
                
                # 检查是否有新的URL（即使数量相同）
                new_urls = current_urls - initial_urls
                if new_urls:
                    self.log(f"[OK] 检测到 {len(new_urls)} 张新图片（URL变化）")
                    # 等待图片完全加载
                    self.log("等待图片稳定加载...")
                    time.sleep(3)  # 缩短等待时间
                    return True
                
                # 方法2：检查数量增加（兼容旧逻辑）
                if current_count > initial_count:
                    self.log(f"[OK] 检测到新增图片 (数量: {initial_count} -> {current_count})")
                    time.sleep(3)
                    return True
                
                # 方法3：使用JavaScript更精确地检测（加入错误处理）
                try:
                    js_result = self.page.evaluate('''
                        () => {
                            try {
                                const images = document.querySelectorAll('img');
                                const blobImages = [];
                                const largeImages = [];
                                
                                images.forEach(img => {
                                    if (img.width > 200 && img.height > 200) {
                                        largeImages.push(img.src);
                                        if (img.src && img.src.startsWith('blob:')) {
                                            blobImages.push(img.src);
                                        }
                                    }
                                });
                                
                                // 简化生成状态检查，避免选择器错误
                                const generating = document.querySelector('[class*="progress"], [class*="loading"], [class*="generating"]');
                                
                                return {
                                    largeCount: largeImages.length,
                                    blobCount: blobImages.length,
                                    urls: largeImages,
                                    isGenerating: !!generating
                                };
                            } catch (e) {
                                return {
                                    largeCount: 0,
                                    blobCount: 0,
                                    urls: [],
                                    isGenerating: false,
                                    error: e.toString()
                                };
                            }
                        }
                    ''')
                except Exception as js_error:
                    # JavaScript执行失败，继续使用其他方法
                    js_result = None
                
                if js_result:
                    # 检查JavaScript返回的URL
                    js_urls = set(js_result.get('urls', []))
                    js_new_urls = js_urls - initial_urls
                    
                    if js_new_urls:
                        self.log(f"[OK] JavaScript检测到 {len(js_new_urls)} 张新图片")
                        time.sleep(3)
                        return True
                    
                    # 如果检测到正在生成，继续等待
                    if js_result.get('isGenerating'):
                        if time.time() - last_log_time > 10:  # 每10秒记录一次
                            self.log("检测到生成进行中，继续等待...")
                            last_log_time = time.time()
                
                # 每10秒输出一次状态
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0 and time.time() - last_log_time > 1:
                    self.log(f"已等待 {elapsed} 秒，当前 {current_count} 张图片...")
                    last_log_time = time.time()
            
            # 超时后做最后一次检查
            self.log("[WARNING] 等待超时，进行最终检查...")
            
            # 最终检查：即使超时也检查是否有URL变化
            final_urls = set()
            images = self.page.query_selector_all('img:visible')
            for img in images:
                try:
                    box = img.bounding_box()
                    if box and box['width'] > 200 and box['height'] > 200:
                        src = img.get_attribute('src')
                        if src:
                            final_urls.add(src)
                except:
                    pass
            
            final_new_urls = final_urls - initial_urls
            if final_new_urls:
                self.log(f"[OK] 最终检查发现 {len(final_new_urls)} 张新图片")
                return True
            
            self.log(f"[WARNING] 确认超时，未检测到新图片（初始: {len(initial_urls)}, 最终: {len(final_urls)}）")
            return False
            
        except Exception as e:
            self.log(f"等待生成失败: {e}")
            return False
    
    def download_image(self, download_all: bool = True, only_new: bool = True):
        """下载图片（使用最稳定的方法：JavaScript获取blob数据）
        
        Args:
            download_all: 是否下载所有图片
            only_new: 是否只下载新图片（避免重复下载）
        """
        downloaded = 0
        
        try:
            self.log("开始下载图片")
            
            # 检查是否应该停止
            if self.is_task_stopped():
                self.log("任务已停止，跳过下载")
                return 0
                
            # 等待图片完全加载
            time.sleep(2)
            
            # 查找所有大图片
            self.log("查找生成的图片...")
            images = self.page.query_selector_all('img:visible')
            large_images = []
            
            for img in images:
                try:
                    box = img.bounding_box()
                    if box and box['width'] > 200 and box['height'] > 200:
                        # 获取图片URL
                        src = img.get_attribute('src')
                        
                        # 检查是否应该下载这张图片
                        should_download = True
                        
                        if only_new:
                            # 1. 检查是否已经下载过
                            if src in self.downloaded_urls:
                                should_download = False
                                self.log(f"跳过已下载的图片: {src[:50]}...")
                            # 2. 检查是否是生成前就存在的图片
                            elif src in self.pre_generation_urls:
                                should_download = False
                                self.log(f"跳过旧图片: {src[:50]}...")
                        
                        if should_download:
                            large_images.append({
                                'element': img,
                                'src': src,
                                'x': box['x'],
                                'y': box['y'],
                                'width': box['width'],
                                'height': box['height']
                            })
                except:
                    pass
            
            if not large_images:
                self.log("未找到新的图片需要下载")
                return 0
            
            self.log(f"找到 {len(large_images)} 张新图片需要下载")
            
            # 按x坐标排序（从左到右）
            sorted_images = sorted(large_images, key=lambda img: img['x'])
            
            # JavaScript函数：获取blob数据
            get_blob_script = '''
                async (img) => {
                    try {
                        const src = img.src;
                        if (!src) return null;
                        
                        let dataUrl = null;
                        
                        if (src.startsWith('blob:')) {
                            // 尝试通过fetch获取blob数据
                            try {
                                const response = await fetch(src);
                                const blob = await response.blob();
                                
                                // 转换为base64
                                return new Promise((resolve) => {
                                    const reader = new FileReader();
                                    reader.onloadend = () => resolve({
                                        success: true,
                                        data: reader.result,
                                        width: img.naturalWidth,
                                        height: img.naturalHeight,
                                        type: blob.type
                                    });
                                    reader.readAsDataURL(blob);
                                });
                            } catch (fetchError) {
                                // 如果fetch失败，使用canvas方法
                                console.log('Fetch failed, using canvas method');
                            }
                        }
                        
                        // 使用canvas方法（备用或主要方法）
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        canvas.width = img.naturalWidth || img.width;
                        canvas.height = img.naturalHeight || img.height;
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        
                        return {
                            success: true,
                            data: canvas.toDataURL('image/jpeg', 0.95),
                            width: canvas.width,
                            height: canvas.height,
                            type: 'image/jpeg'
                        };
                    } catch (error) {
                        return {
                            success: false,
                            error: error.toString()
                        };
                    }
                }
            '''
            
            # 下载所有图片
            for i, img_info in enumerate(sorted_images):
                # 检查是否应该停止
                if self.is_task_stopped():
                    self.log("任务已停止，中断下载")
                    break
                
                try:
                    img_element = img_info['element']
                    position = "左侧" if i == 0 else "右侧" if i == 1 else f"图{i+1}"
                    
                    self.log(f"处理图片 ({position})...")
                    
                    # 使用JavaScript获取图片数据
                    blob_data = self.page.evaluate(get_blob_script, img_element)
                    
                    if blob_data and blob_data.get('success'):
                        # 成功获取图片数据
                        self.log(f"成功获取图片数据 ({blob_data['width']}x{blob_data['height']})")
                        
                        # 生成文件名
                        with self.lock:
                            self.downloaded_count += 1
                            count = self.downloaded_count
                        
                        filename = f"whisk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{count}_{position}.jpg"
                        save_path = self.save_directory / filename
                        
                        # 从base64保存图片
                        if blob_data['data'] and blob_data['data'].startswith('data:'):
                            import base64
                            img_data = blob_data['data'].split(',')[1]
                            img_bytes = base64.b64decode(img_data)
                            save_path.write_bytes(img_bytes)
                            downloaded += 1
                            
                            size_kb = save_path.stat().st_size / 1024
                            self.log(f"[OK] 保存成功 ({position}): {filename} ({size_kb:.1f} KB)")
                            
                            # 记录已下载的URL，避免重复下载
                            if 'src' in img_info:
                                self.downloaded_urls.add(img_info['src'])
                            
                            # 更新下载进度
                            self.update_download_progress()
                        else:
                            self.log(f"[WARNING] 图片数据格式错误")
                    else:
                        # JavaScript方法失败，使用截图备用方案
                        self.log(f"[WARNING] 获取blob数据失败: {blob_data.get('error', '未知错误')}")
                        self.log(f"使用截图方法保存 ({position})...")
                        
                        with self.lock:
                            self.downloaded_count += 1
                            count = self.downloaded_count
                        
                        filename = f"whisk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{count}_{position}.jpg"
                        save_path = self.save_directory / filename
                        img_element.screenshot(path=str(save_path))
                        downloaded += 1
                        
                        size_kb = save_path.stat().st_size / 1024
                        self.log(f"[OK] 截图保存成功 ({position}): {filename} ({size_kb:.1f} KB)")
                        
                        # 记录已下载的URL
                        if 'src' in img_info:
                            self.downloaded_urls.add(img_info['src'])
                        
                        self.update_download_progress()
                    
                    # 短暂延迟
                    time.sleep(1)
                    
                except Exception as e:
                    self.log(f"[WARNING] 处理图片 {i+1} 时出错: {e}")
                    
                    # 最后的备用方案：直接截图
                    try:
                        with self.lock:
                            self.downloaded_count += 1
                            count = self.downloaded_count
                        
                        filename = f"whisk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{count}_{position}.jpg"
                        save_path = self.save_directory / filename
                        img_element.screenshot(path=str(save_path))
                        downloaded += 1
                        
                        self.log(f"[OK] 备用截图成功 ({position}): {filename}")
                        
                        # 记录已下载的URL
                        if 'src' in img_info:
                            self.downloaded_urls.add(img_info['src'])
                        
                        self.update_download_progress()
                    except:
                        self.log(f"[ERROR] 所有方法都失败了")
            
            return downloaded
            
        except Exception as e:
            self.log(f"下载过程出错: {e}")
            return downloaded
    
    def generate_images(self, prompt: str, count: int, aspect_ratio: str = "1:1", 
                       min_delay: int = 5, max_delay: int = 8):
        """生成多张图片的主流程"""
        try:
            with self.lock:
                self.is_running = True
                self.should_stop = False
                # 预期每次生成2张图片
                self.total_images_expected = count * 2
                # 记录任务开始时的下载计数
                self.task_start_count = self.downloaded_count
            
            self.log(f"开始生成任务: {count} 次生成, 比例 {aspect_ratio} (每次生成2张图片)")
            self.log(f"预期总下载数: {self.total_images_expected} 张图片")
            self.log(f"[调试] 任务初始化 - 下载计数: {self.downloaded_count}, 预期: {self.total_images_expected}")
            
            # 选择纵横比（每次任务开始时设置一次）
            if aspect_ratio != "1:1":  # 如果不是默认比例
                self.select_aspect_ratio(aspect_ratio)
                time.sleep(2)  # 等待设置生效
            
            # 生成图片 - 真正按下载数量完成
            generation_attempt = 0
            max_attempts = count * 3  # 最多尝试次数，防止无限循环
            
            while generation_attempt < max_attempts:
                generation_attempt += 1
                
                # 检查是否应该停止
                if self.is_task_stopped():
                    self.log("任务已被停止")
                    break
                
                # 检查是否已达到预期下载数量
                with self.lock:
                    current_downloaded = self.downloaded_count - self.task_start_count
                    target_downloaded = self.total_images_expected
                
                self.log(f"[调试] 尝试第 {generation_attempt} 次生成 - 已下载: {current_downloaded}/{target_downloaded}")
                
                if current_downloaded >= target_downloaded:
                    self.log(f"[COMPLETE] 已达到预期下载数量 {target_downloaded} 张，任务完成！")
                    break
                
                remaining_needed = target_downloaded - current_downloaded
                self.log(f"\n--- 第 {generation_attempt} 次生成尝试 (已下载: {current_downloaded}, 还需: {remaining_needed} 张) ---")
                self.update_progress(current_downloaded, target_downloaded, 'download')
                
                # 输入提示词
                self.input_prompt(prompt)
                
                # 触发生成
                self.trigger_generation()
                
                # 等待生成
                generation_success = self.wait_for_generation()
                
                # 无论是否"超时"，都尝试下载（可能有新图片）
                if generation_success:
                    self.log(f"生成检测成功，开始下载...")
                else:
                    self.log(f"[WARNING] 等待检测超时，但仍尝试下载可能的新图片...")
                
                # 始终尝试下载（即使等待"超时"）
                downloaded = self.download_image()
                if downloaded > 0:
                    with self.lock:
                        new_total = self.downloaded_count - self.task_start_count
                    self.log(f"[OK] 第 {generation_attempt} 次尝试，下载了 {downloaded} 张图片 (本任务总计: {new_total}/{target_downloaded})")
                    
                    # 检查是否已完成目标
                    if new_total >= target_downloaded:
                        self.log(f"[COMPLETE] 已达到预期下载数量 {target_downloaded} 张，任务完成！")
                        break
                else:
                    if generation_success:
                        self.log(f"[WARNING] 第 {generation_attempt} 次生成下载失败")
                    else:
                        self.log(f"[INFO] 第 {generation_attempt} 次尝试未发现新图片")
                
                # 延迟（只有在未达到目标且未停止时才延迟）
                if not self.is_task_stopped():
                    with self.lock:
                        current_task_downloaded = self.downloaded_count - self.task_start_count
                    
                    if current_task_downloaded < self.total_images_expected:
                        delay = random.randint(min_delay, max_delay)
                        self.log(f"等待 {delay} 秒...")
                        
                        # 分段延迟，以便及时响应停止请求和完成检查
                        for _ in range(delay):
                            if self.is_task_stopped():
                                self.log("延迟期间收到停止请求")
                                break
                            with self.lock:
                                current_task_downloaded = self.downloaded_count - self.task_start_count
                                if current_task_downloaded >= self.total_images_expected:
                                    self.log("延迟期间检测到任务已完成")
                                    break
                            time.sleep(1)
                    else:
                        self.log("已达到目标，结束任务")
                        break
            
            self.log(f"[调试] 生成循环结束 - 总尝试次数: {generation_attempt}/{max_attempts}")
            
            with self.lock:
                self.is_running = False
            
            # 最终状态检查
            with self.lock:
                final_downloaded = self.downloaded_count - self.task_start_count  # 本任务实际下载数
                target_downloaded = self.total_images_expected
            
            if self.is_task_stopped():
                self.log(f"\n[WARNING] 任务已停止！已下载 {final_downloaded}/{target_downloaded} 张图片")
            elif final_downloaded >= target_downloaded:
                self.update_progress(target_downloaded, target_downloaded, 'download')
                self.log(f"\n[SUCCESS] 任务完成！成功下载 {final_downloaded} 张图片，达到预期目标 {target_downloaded} 张")
            else:
                self.log(f"\n[WARNING] 任务结束！已下载 {final_downloaded}/{target_downloaded} 张图片，未达到预期目标")
            
            self.log(f"保存位置: {self.save_directory}")
            
        except Exception as e:
            with self.lock:
                self.is_running = False
            self.log(f"[ERROR] 生成过程出错: {e}")
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
    
    def refresh_page(self):
        """刷新页面"""
        try:
            self.log("刷新页面...")
            self.page.reload()
            time.sleep(3)  # 等待页面加载

            # 检查是否在 Whisk 页面
            current_url = self.page.url
            if "whisk/project" not in current_url and "whisk" not in current_url:
                self.log("页面跳转异常，重新导航到 Whisk...")
                self.page.goto("https://labs.google/fx/tools/whisk")
                time.sleep(3)

            self.log("[OK] 页面刷新完成")

            # 清空已记录的图片URL，因为页面刷新后都是新的
            self.downloaded_urls.clear()
            self.pre_generation_urls.clear()

        except Exception as e:
            self.log(f"刷新页面失败: {e}")
            raise

    def reopen_page(self):
        """关闭当前页面并重新打开新的Whisk页面"""
        try:
            self.log("关闭当前页面并重新打开...")

            # 关闭当前页面
            if self.page:
                self.page.close()
                self.log("已关闭当前页面")

            # 创建新页面
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                self.page = context.new_page()
                self.log("创建新页面成功")

                # 导航到 Whisk 项目页面
                self.log("导航到 Whisk 项目页面...")
                self.page.goto("https://labs.google/fx/tools/whisk/project")

                # 等待页面完全加载
                time.sleep(5)

                # 检查页面是否正确加载
                current_url = self.page.url
                if "whisk" not in current_url:
                    self.log("页面加载异常，重新尝试...")
                    self.page.goto("https://labs.google/fx/tools/whisk/project")
                    time.sleep(3)

                self.log(f"[OK] 成功打开新页面: {self.page.url}")

                # 清空已记录的图片URL，因为是新页面
                self.downloaded_urls.clear()
                self.pre_generation_urls.clear()

            else:
                raise Exception("浏览器没有可用的上下文")

        except Exception as e:
            self.log(f"重新打开页面失败: {e}")
            raise

    def run_queue(self, task_queue: list, min_delay: int = 5, max_delay: int = 8):
        """执行任务队列（串行执行多个任务）

        Args:
            task_queue: 任务队列，每个任务是一个字典，包含：
                - prompt: 提示词
                - count: 生成数量
                - aspect_ratio: 纵横比
                - task_name: 任务名称（可选）
            min_delay: 最小延迟时间
            max_delay: 最大延迟时间
        """
        try:
            # 连接浏览器（只连接一次）
            self.connect_browser()

            total_tasks = len(task_queue)
            self.log(f"开始执行任务队列，共 {total_tasks} 个任务")

            for idx, task in enumerate(task_queue, 1):
                # 发送队列进度更新
                if self.progress_callback:
                    self.progress_callback(idx-1, total_tasks, 'queue')

                # 检查是否应该停止
                if self.is_task_stopped():
                    self.log(f"任务队列已停止，已完成 {idx-1}/{total_tasks} 个任务")
                    break

                # 提取任务参数
                prompt = task.get('prompt', '')
                count = task.get('count', 1)
                aspect_ratio = task.get('aspect_ratio', '1:1')
                task_name = task.get('task_name', f'任务{idx}')
                task_save_dir = task.get('save_directory', None)

                self.log(f"\n========== 执行队列任务 {idx}/{total_tasks}: {task_name} ==========")
                self.log(f"提示词: {prompt[:50]}...")
                self.log(f"数量: {count}, 纵横比: {aspect_ratio}")

                # 如果任务有独立的保存目录，更新保存路径
                if task_save_dir:
                    self.save_directory = Path(task_save_dir)
                    self.save_directory.mkdir(exist_ok=True, parents=True)
                    self.log(f"保存目录: {task_save_dir}")

                # 如果不是第一个任务，关闭页面并重新打开新页面
                if idx > 1:
                    self.reopen_page()
                    # 重新打开后等待一下
                    time.sleep(2)

                # 执行任务
                try:
                    self.generate_images(prompt, count, aspect_ratio, min_delay, max_delay)
                    self.log(f"[COMPLETE] 任务 {task_name} 完成")
                except Exception as task_error:
                    self.log(f"[ERROR] 任务 {task_name} 执行失败: {task_error}")
                    # 继续执行下一个任务
                    continue

                # 更新队列进度（任务完成）
                if self.progress_callback:
                    self.progress_callback(idx, total_tasks, 'queue')

                # 任务间延迟（除了最后一个任务）
                if idx < total_tasks and not self.is_task_stopped():
                    delay = random.randint(3, 5)
                    self.log(f"等待 {delay} 秒后执行下一个任务...")
                    for _ in range(delay):
                        if self.is_task_stopped():
                            break
                        time.sleep(1)

            # 队列执行完成
            if not self.is_task_stopped():
                self.log(f"\n[SUCCESS] 任务队列执行完成！共完成 {total_tasks} 个任务")
                # 发送最终进度
                if self.progress_callback:
                    self.progress_callback(total_tasks, total_tasks, 'queue')

        except Exception as e:
            self.log(f"执行任务队列失败: {e}")
            raise
        finally:
            # 清理资源
            self.cleanup()

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