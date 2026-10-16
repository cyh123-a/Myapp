# -*- coding: utf-8 -*-
"""
股票涨跌幅实时显示 App
======================
功能: 在手机屏幕实时显示1-3只股票的涨跌幅
数据源: 腾讯财经API(首选) / 新浪财经API(备选)
打包: buildozer -> Android APK
手机: 一加Ace5 (Android)
"""

import kivy
kivy.require('2.3.0')

import os
import re
import json
import time
import threading
from datetime import datetime, timedelta, time as dt_time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

import requests

# ==================== 配置 ====================
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_settings.json')

DEFAULT_SETTINGS = {
    'stocks': 'sh600519,sz000001,sh000001',
    'api_source': 'tencent',
    'refresh_interval': 10,
    'trading_hours_only': True,
    'all_day_display': False,
    'screen_off_pause': True,
}

# ==================== 设置管理 ====================
def load_settings():
    """加载设置，不存在则返回默认值"""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in saved:
                    saved[k] = v
            return saved
    except Exception as e:
        print(f"加载设置失败: {e}，使用默认设置")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """保存设置到文件"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print("设置已保存")
    except Exception as e:
        print(f"保存设置失败: {e}")

# ==================== API 数据获取 ====================
def fetch_tencent(stocks):
    """
    腾讯财经API获取股票数据
    接口: https://qt.gtimg.cn/q=sh600519,sz000001
    返回格式: v_code="field0~field1~...";
    字段分隔符: ~
    编码: GBK
    
    通过查找时间戳(14位数字)来定位涨跌幅字段:
    - 时间戳后第1个字段 = 涨跌额
    - 时间戳后第2个字段 = 涨跌幅(%)
    """
    codes = [s.strip() for s in stocks.split(',') if s.strip()]
    if not codes:
        return None
    
    url = 'https://qt.gtimg.cn/q={}'.format(','.join(codes))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        
        results = []
        lines = resp.text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 解析: v_sh600519="字段数据";
            match = re.match(r'v_(\w+)="([^"]*)";', line)
            if match:
                code = match.group(1)
                data = match.group(2)
                fields = data.split('~')
                
                # 股票名称(字段1)
                name = fields[1] if len(fields) > 1 and fields[1] else code
                
                # 通过查找时间戳(14位数字如20261015161456)来定位涨跌幅
                timestamp_idx = None
                for i, f in enumerate(fields):
                    if re.match(r'^\d{14}$', f):
                        timestamp_idx = i
                        break
                
                # 涨跌幅 = 时间戳后第2个字段
                change_pct = 0.0
                if timestamp_idx is not None and timestamp_idx + 2 < len(fields):
                    try:
                        change_pct = float(fields[timestamp_idx + 2])
                    except (ValueError, TypeError):
                        change_pct = 0.0
                
                results.append({
                    'code': code,
                    'name': name,
                    'change_pct': change_pct,
                })
        return results
    except Exception as e:
        print(f"腾讯API错误: {e}")
        return None

def fetch_sina(stocks):
    """
    新浪财经API获取股票数据
    接口: http://hq.sinajs.cn/list=sh600519,sz000001
    返回格式: var hq_str_code="name,open,preclose,current,high,low,...";
    字段分隔符: ,
    编码: GBK
    要求: 需设置 Referer: http://finance.sina.com.cn
    
    A股字段顺序:
    0-股票名称, 1-今日开盘价, 2-昨日收盘价, 3-当前价格, ...
    涨跌幅 = (当前价格 - 昨日收盘价) / 昨日收盘价 * 100
    """
    codes = [s.strip() for s in stocks.split(',') if s.strip()]
    if not codes:
        return None
    
    url = 'http://hq.sinajs.cn/list={}'.format(','.join(codes))
    headers = {
        'Referer': 'http://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        
        results = []
        lines = resp.text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 解析: var hq_str_sh600519="贵州茅台,1286.00,1286.00,1312.97,...";
            match = re.match(r'var hq_str_(\w+)="([^"]*)";', line)
            if match:
                code = match.group(1)
                data = match.group(2)
                fields = data.split(',')
                # fields[0]=名称, fields[2]=昨收, fields[3]=现价
                if len(fields) >= 4 and fields[0]:
                    name = fields[0]
                    try:
                        preclose = float(fields[2])
                        current = float(fields[3])
                    except (ValueError, TypeError):
                        preclose = 0
                        current = 0
                    
                    if preclose > 0:
                        change_pct = (current - preclose) / preclose * 100
                    else:
                        change_pct = 0.0
                    
                    results.append({
                        'code': code,
                        'name': name,
                        'change_pct': change_pct,
                    })
        return results
    except Exception as e:
        print(f"新浪API错误: {e}")
        return None

def fetch_stock_data(settings):
    """获取股票数据，按设置选择API源，失败时自动切换备选"""
    source = settings.get('api_source', 'tencent')
    stocks = settings.get('stocks', '')
    
    # 按优先级尝试API
    if source == 'tencent':
        data = fetch_tencent(stocks)
        if data and len(data) > 0:
            return data
        # 腾讯失败，尝试新浪
        print("腾讯API失败，尝试新浪API...")
        return fetch_sina(stocks)
    else:
        # 首选新浪
        data = fetch_sina(stocks)
        if data and len(data) > 0:
            return data
        # 新浪失败，尝试腾讯
        print("新浪API失败，尝试腾讯API...")
        return fetch_tencent(stocks)

# ==================== 交易时间判断 ====================
def is_trading_time(settings):
    """判断当前是否在交易时间内"""
    now = datetime.now()
    
    # 周末不交易
    if now.weekday() >= 5:
        return False
    
    # 如果勾选了全天显示，不限制时间
    if settings.get('all_day_display', False):
        return True
    
    # 默认交易时间: 9:15-11:35, 12:55-15:30
    current_time = now.time()
    trading_periods = [
        (dt_time(9, 15), dt_time(11, 35)),
        (dt_time(12, 55), dt_time(15, 30)),
    ]
    
    for start, end in trading_periods:
        if start <= current_time <= end:
            return True
    return False

def should_show_data(settings):
    """判断是否应该显示数据"""
    if settings.get('all_day_display', False):
        return True
    return is_trading_time(settings)

# ==================== Kivy App ====================
class StockDisplayApp(App):
    def __init__(self, **kwargs):
        super(StockDisplayApp, self).__init__(**kwargs)
        self.settings = load_settings()
        self.stock_data = []
        self.last_fetch_time = 0
        self.refresh_timer = None
        self.ui_update_timer = None
    
    def build(self):
        # 设置窗口
        Window.clearcolor = get_color_from_hex('#FFFFFF')
        
        # 主布局 - 垂直排列
        self.main_layout = BoxLayout(
            orientation='vertical',
            padding=[10, 20, 10, 10],
            spacing=10,
        )
        
        # 顶部标题栏
        title_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.06),
            spacing=5,
        )
        self.title_label = Label(
            text='股票涨跌幅实时显示',
            font_size='16sp',
            bold=True,
            color=get_color_from_hex('#333333'),
        )
        title_layout.add_widget(self.title_label)
        
        # 设置按钮
        self.settings_btn = Button(
            text='设置',
            font_size='14sp',
            size_hint=(0.2, 1),
            background_color=get_color_from_hex('#4CAF50'),
            color=get_color_from_hex('#FFFFFF'),
        )
        self.settings_btn.bind(on_press=self.open_settings)
        title_layout.add_widget(self.settings_btn)
        
        # 刷新按钮
        self.refresh_btn = Button(
            text='刷新',
            font_size='14sp',
            size_hint=(0.2, 1),
            background_color=get_color_from_hex('#2196F3'),
            color=get_color_from_hex('#FFFFFF'),
        )
        self.refresh_btn.bind(on_press=self.manual_refresh)
        title_layout.add_widget(self.refresh_btn)
        
        self.main_layout.add_widget(title_layout)
        
        # 股票数据显示区域
        self.stock_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.7),
            padding=[5, 5, 5, 5],
            spacing=8,
        )
        self.main_layout.add_widget(self.stock_container)
        
        # 底部状态栏
        status_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.15),
            padding=[3, 3, 3, 3],
            spacing=3,
        )
        
        self.status_label = Label(
            text='正在初始化...',
            font_size='11sp',
            color=get_color_from_hex('#888888'),
            halign='center',
        )
        status_layout.add_widget(self.status_label)
        
        self.time_label = Label(
            text='',
            font_size='10sp',
            color=get_color_from_hex('#AAAAAA'),
            halign='center',
        )
        status_layout.add_widget(self.time_label)
        
        self.main_layout.add_widget(status_layout)
        
        # 构建界面
        self.root = self.main_layout
        
        # 启动定时器
        self._start_timers()
        
        # 首次获取数据
        self._fetch_data_thread()
        
        return self.root
    
    def _start_timers(self):
        """启动UI更新和数据获取定时器"""
        interval = max(self.settings.get('refresh_interval', 10), 5)
        
        # UI更新定时器 (每秒更新时钟显示)
        self.ui_update_timer = Clock.schedule_interval(self._update_clock, 1)
        
        # 数据获取定时器
        self.refresh_timer = Clock.schedule_interval(self._fetch_data_thread, interval)
        
        self.status_label.text = '定时器已启动, 间隔{}秒'.format(interval)
    
    def _update_clock(self, dt):
        """更新时钟显示"""
        now = datetime.now()
        self.time_label.text = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新交易时间状态
        if should_show_data(self.settings):
            trading = is_trading_time(self.settings)
            if trading:
                self.status_label.text = '交易时间内 | 下次刷新: 等待中'
            else:
                self.status_label.text = '非交易时间 | 全天显示: {}'.format(
                    '开' if self.settings.get('all_day_display') else '关'
                )
    
    def _fetch_data_thread(self, dt=None):
        """后台线程获取股票数据"""
        # 检查是否应该显示
        if not should_show_data(self.settings):
            self.stock_data = []
            self._update_display()
            self.status_label.text = '非交易时间，暂停显示'
            return
        
        # 获取数据
        data = fetch_stock_data(self.settings)
        
        if data:
            self.stock_data = data
            self.last_fetch_time = time.time()
            # 在主线程更新UI
            Clock.schedule_once(lambda dt: self._update_display(), 0)
            self.status_label.text = '数据已更新 | 间隔{}秒'.format(
                self.settings.get('refresh_interval', 10)
            )
        else:
            self.status_label.text = '数据获取失败，请稍后重试'
    
    def _update_display(self):
        """更新界面显示"""
        # 清空容器
        for child in self.stock_container.children[:]:
            self.stock_container.remove_widget(child)
        
        if not self.stock_data:
            no_data_label = Label(
                text='暂无数据',
                font_size='24sp',
                color=get_color_from_hex('#999999'),
                halign='center',
                valign='middle',
            )
            no_data_label.size_hint = (1, 1)
            self.stock_container.add_widget(no_data_label)
            return
        
        # 为每只股票创建显示标签
        for i, stock in enumerate(self.stock_data):
            change = stock['change_pct']
            
            # 颜色: 涨=红色, 跌=绿色, 平=灰色
            if change > 0:
                color_hex = '#E53935'  # 红色 - 上涨
                sign = '+'
            elif change < 0:
                color_hex = '#43A047'  # 绿色 - 下跌
                sign = ''
            else:
                color_hex = '#666666'  # 灰色 - 平
                sign = '+'
            
            # 格式化涨跌幅
            pct_str = '{}{:.2f}%'.format(sign, change)
            
            # 创建股票显示布局
            stock_layout = BoxLayout(
                orientation='horizontal',
                size_hint=(1, None),
                height=60,
                spacing=10,
                padding=[10, 5, 10, 5],
            )
            
            # 股票名称标签
            name_label = Label(
                text=stock['name'],
                font_size='20sp',
                bold=True,
                color=get_color_from_hex('#333333'),
                valign='center',
            )
            stock_layout.add_widget(name_label)
            
            # 涨跌幅标签 (带颜色)
            change_label = Label(
                text=pct_str,
                font_size='24sp',
                bold=True,
                color=get_color_from_hex(color_hex),
                valign='center',
            )
            stock_layout.add_widget(change_label)
            
            # 添加分隔符 "-" (不是最后一只股票)
            if i < len(self.stock_data) - 1:
                sep_label = Label(
                    text='  -  ',
                    font_size='20sp',
                    color=get_color_from_hex('#AAAAAA'),
                    valign='center',
                )
                stock_layout.add_widget(sep_label)
            
            self.stock_container.add_widget(stock_layout)
        
        # 显示更新信息
        code_list = [s['code'] for s in self.stock_data]
        self.status_label.text = '更新: {} | {}只股票'.format(
            datetime.now().strftime('%H:%M:%S'),
            len(self.stock_data)
        )
    
    def manual_refresh(self, instance):
        """手动刷新数据"""
        self.status_label.text = '手动刷新中...'
        self._fetch_data_thread()
    
    def open_settings(self, instance):
        """打开设置弹窗"""
        content = BoxLayout(
            orientation='vertical',
            padding=[15, 15, 15, 15],
            spacing=12,
        )
        
        # 股票代码
        label1 = Label(text='股票代码 (逗号分隔):', font_size='12sp', bold=True)
        input_stocks = TextInput(
            text=self.settings.get('stocks', ''),
            multiline=False,
            font_size='12sp',
            hint_text='例: sh600519,sz000001,sh000001',
        )
        
        # API源
        label2 = Label(text='数据源 (tencent/sina):', font_size='12sp', bold=True)
        input_api = TextInput(
            text=self.settings.get('api_source', 'tencent'),
            multiline=False,
            font_size='12sp',
            hint_text='tencent 或 sina',
        )
        
        # 刷新间隔
        label3 = Label(text='刷新间隔 (秒, 最小5秒):', font_size='12sp', bold=True)
        input_interval = TextInput(
            text=str(self.settings.get('refresh_interval', 10)),
            multiline=False,
            font_size='12sp',
            input_filter='int',
            hint_text='例: 10',
        )
        
        # 复选框
        chk_trading = CheckBox(
            label='仅交易时间显示',
            state='on' if self.settings.get('trading_hours_only', True) else 'off',
            font_size='12sp',
        )
        chk_all_day = CheckBox(
            label='全天显示 (忽略交易时间)',
            state='on' if self.settings.get('all_day_display', False) else 'off',
            font_size='12sp',
        )
        chk_screen = CheckBox(
            label='黑屏暂停刷新',
            state='on' if self.settings.get('screen_off_pause', True) else 'off',
            font_size='12sp',
        )
        
        # 提示文字
        hint_label = Label(
            text=(
                '提示:\n'
                '  上证指数: sh000001\n'
                '  深证成指: sz399001\n'
                '  贵州茅台: sh600519\n'
                '  平安银行: sz000001\n'
                '  比亚迪: sz002594\n'
                '  沪市股票前加sh, 深市前加sz'
            ),
            font_size='10sp',
            color=get_color_from_hex('#666666'),
        )
        
        # 保存按钮
        save_btn = Button(
            text='保存设置',
            font_size='14sp',
            background_color=get_color_from_hex('#4CAF50'),
            color=get_color_from_hex('#FFFFFF'),
            size_hint=(1, 0.1),
        )
        save_btn.bind(on_press=lambda dt: self._save_settings(
            input_stocks.text,
            input_api.text,
            input_interval.text,
            chk_trading.state,
            chk_all_day.state,
            chk_screen.state,
        ))
        
        content.extend([
            label1, input_stocks,
            label2, input_api,
            label3, input_interval,
            chk_trading, chk_all_day, chk_screen,
            hint_label,
            save_btn,
        ])
        
        popup = Popup(
            title='设置',
            content=content,
            size_hint=(0.95, 0.85),
        )
        self._settings_popup = popup
        popup.open()
    
    def _save_settings(self, stocks, api_source, interval, trading, all_day, screen):
        """保存设置并重启定时器"""
        # 解析刷新间隔
        try:
            interval_val = int(interval)
            if interval_val < 5:
                interval_val = 5
        except (ValueError, TypeError):
            interval_val = 10
        
        new_settings = {
            'stocks': stocks if stocks else 'sh600519,sz000001,sh000001',
            'api_source': api_source if api_source in ('tencent', 'sina') else 'tencent',
            'refresh_interval': interval_val,
            'trading_hours_only': trading == 'on',
            'all_day_display': all_day == 'on',
            'screen_off_pause': screen == 'on',
        }
        
        # 保存
        save_settings(new_settings)
        self.settings = new_settings
        
        # 重启定时器
        if self.refresh_timer:
            self.refresh_timer.cancel()
        if self.ui_update_timer:
            self.ui_update_timer.cancel()
        
        self._start_timers()
        
        # 立即获取一次数据
        self._fetch_data_thread()
        
        # 关闭弹窗
        if hasattr(self, '_settings_popup'):
            self._settings_popup.dismiss()
        
        self.status_label.text = '设置已保存'
    
    def on_stop(self):
        """应用停止时"""
        print("App stopped")
    
    def on_resume(self):
        """应用恢复时"""
        print("App resumed")
        self._fetch_data_thread()


# ==================== 入口 ====================
if __name__ == '__main__':
    StockDisplayApp().run()
