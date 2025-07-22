#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试任务模块
用于验证通用任务调度引擎的功能
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# 配置日志
def setup_logger():
    """设置日志记录器"""
    logger = logging.getLogger('test_task')
    logger.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    return logger

def print_fancy_config(env_vars, logger):
    """以美观的格式打印环境变量配置"""
    logger.info("=" * 50)
    logger.info("测试任务配置")
    logger.info("=" * 50)
    
    # 按类别分组显示配置
    categories = {
        "任务信息": ["TASK_"],
        "参数设置": ["PARAM"],
        "显示设置": ["DISPLAY_"]
    }
    
    for category, prefixes in categories.items():
        logger.info(f"【{category}】")
        has_items = False
        
        for key, value in env_vars.items():
            if any(key.startswith(prefix) for prefix in prefixes):
                logger.info(f"  {key} = {value}")
                has_items = True
        
        if has_items:
            logger.info("-" * 50)
    
    # 显示未分类的配置项
    other_items = {k: v for k, v in env_vars.items() 
                  if not any(k.startswith(p) for c in categories.values() for p in c)}
    
    if other_items:
        logger.info("【其他设置】")
        for key, value in other_items.items():
            logger.info(f"  {key} = {value}")
        logger.info("-" * 50)
    
    logger.info("配置加载完成")
    logger.info("=" * 50)

def main():
    """主函数"""
    
    # 设置日志记录器
    logger = setup_logger()
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"任务开始执行: {start_time}")
    
    # 收集环境变量配置
    env_config = {k: v for k, v in os.environ.items() if k.startswith(('TASK_', 'PARAM', 'DISPLAY_'))}
    
    # 打印配置
    print_fancy_config(env_config, logger)
    
    # 记录传入的参数
    logger.info("传入的命令行参数:")
    for i, arg in enumerate(sys.argv):
        logger.info(f"  参数 {i}: {arg}")
    
    # 记录所有环境变量
    logger.info("所有环境变量:")
    for key, value in sorted(os.environ.items()):
        if key.startswith(('TASK_', 'PARAM', 'DISPLAY_')):
            logger.info(f"  {key} = {value}")
    
    # 模拟任务执行
    logger.info("正在执行任务...")
    time.sleep(2)  # 模拟任务执行时间
    
    # 记录结束时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"任务执行完成: {end_time}")
    logger.info(f"执行时长: {duration:.2f} 秒")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())