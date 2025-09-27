#!/usr/bin/env python3
"""
时区调试脚本 - 检查时间过滤问题
"""
import os
import asyncio
from datetime import datetime, timezone, timedelta

# 设置环境变量
os.environ['TZ'] = 'Asia/Shanghai'

def debug_timezone():
    """调试时区问题"""
    print("=== 时区调试信息 ===")
    
    # 当前时间（不同时区）
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()
    
    print(f"UTC当前时间: {utc_now}")
    print(f"系统本地时间: {local_now}")
    
    # 尝试使用pytz
    try:
        import pytz
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        shanghai_now = datetime.now(shanghai_tz)
        print(f"上海时区时间: {shanghai_now}")
        
        # 计算UTC和上海时区的今天开始时间
        utc_today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)
        shanghai_today_start = shanghai_now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"\nUTC今天开始时间: {utc_today_start}")
        print(f"上海今天开始时间: {shanghai_today_start}")
        
        # 时差
        time_diff = shanghai_now - utc_now
        print(f"时差: {time_diff}")
        
        # 模拟消息时间（今天凌晨2点的消息）
        message_time_local = shanghai_now.replace(hour=2, minute=0, second=0, microsecond=0)
        message_time_utc = message_time_local.astimezone(pytz.UTC)
        
        print(f"\n模拟消息时间（上海2点）: {message_time_local}")
        print(f"转换为UTC: {message_time_utc}")
        
        # 检查过滤条件
        print(f"\n=== 过滤条件检查 ===")
        print(f"消息时间 >= UTC今天开始: {message_time_utc >= utc_today_start}")
        print(f"消息时间 >= 上海今天开始: {message_time_local >= shanghai_today_start}")
        
        # 问题分析
        print(f"\n=== 问题分析 ===")
        print("当前代码逻辑：")
        print("1. 消息时间转为UTC")
        print("2. 当前时间使用UTC")
        print("3. 比较 message_time_utc >= utc_today_start")
        print()
        print("问题：UTC的今天开始时间比上海时间晚8小时")
        print("解决：应该使用上海时区的今天开始时间")
        
    except ImportError:
        print("pytz 未安装")

if __name__ == "__main__":
    debug_timezone()
