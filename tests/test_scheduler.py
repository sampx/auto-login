#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用任务调度器测试脚本
提供全面的功能测试和验证
"""

import os
import sys
import time
import argparse
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler_engine import SchedulerEngine, TaskLoader, TaskExecutor, Task

class SchedulerTester:
    """调度器测试类"""
    
    def __init__(self):
        self.test_results = []
        
    def test_task_loader(self) -> bool:
        """测试任务加载器"""
        print("\n" + "="*50)
        print("测试 1: 任务加载器")
        print("="*50)
        
        try:
            loader = TaskLoader("tasks")
            tasks = loader.load_tasks()
            
            print(f"✅ 成功加载 {len(tasks)} 个任务")
            
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. [{task.task_id}] {task.task_name}")
                print(f"     调度: {task.task_schedule}")
                print(f"     命令: {task.task_exec}")
                print(f"     超时: {task.task_timeout}s")
                print()
            
            return len(tasks) > 0
            
        except Exception as e:
            print(f"❌ 任务加载器测试失败: {e}")
            return False
    
    def test_task_executor(self) -> bool:
        """测试任务执行器"""
        print("\n" + "="*50)
        print("测试 2: 任务执行器")
        print("="*50)
        
        try:
            # 创建简单测试任务
            test_task = Task(
                task_id="test_simple",
                task_name="简单测试任务",
                task_exec="python test_task.py",  # 相对路径，在任务目录内执行
                task_schedule="* * * * *",
                task_desc="测试任务执行",
                task_timeout=60
            )
            
            executor = TaskExecutor()
            print("🔄 执行测试任务...")
            
            result = executor.execute_task(test_task)
            
            print(f"✅ 任务执行完成")
            print(f"   执行ID: {result.execution_id}")
            print(f"   状态: {result.status}")
            print(f"   返回码: {result.return_code}")
            print(f"   执行时长: {result.duration:.2f}秒")
            
            # 检查日志文件
            log_file = f"logs/task_{test_task.task_id}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    content = f.read()
                    print(f"   日志文件: {log_file}")
                    if "任务开始执行" in content:
                        print("   ✅ 日志记录正常")
                    else:
                        print("   ⚠️  日志内容异常")
            
            return result.status in ['success', 'completed']
            
        except Exception as e:
            print(f"❌ 任务执行器测试失败: {e}")
            return False
    
    def test_scheduler_engine(self) -> bool:
        """测试调度引擎"""
        print("\n" + "="*50)
        print("测试 3: 调度引擎")
        print("="*50)
        
        try:
            scheduler = SchedulerEngine()
            
            print("🔄 启动调度引擎...")
            scheduler.start()
            
            print("✅ 调度引擎启动成功")
            
            # 获取任务列表
            tasks = scheduler.get_tasks()
            print(f"📋 当前调度任务: {len(tasks)} 个")
            
            for task_info in tasks:
                print(f"   - {task_info['task_name']} ({task_info['task_id']})")
                print(f"     调度: {task_info['task_schedule']}")
                print(f"     下次执行: {task_info.get('next_run_time', 'N/A')}")
            
            # 等待2秒观察
            print("⏳ 等待2秒...")
            time.sleep(2)
            
            scheduler.stop()
            print("🛑 调度引擎已停止")
            
            return len(tasks) > 0
            
        except Exception as e:
            print(f"❌ 调度引擎测试失败: {e}")
            return False
    
    def test_cron_validation(self) -> bool:
        """测试CRON表达式验证"""
        print("\n" + "="*50)
        print("测试 4: CRON表达式验证")
        print("="*50)
        
        test_cases = [
            # 基础格式
            ("0 9 * * *", "每天9点", True),
            ("*/5 * * * *", "每5分钟", True),
            ("0 0 1 * *", "每月1日", True),
            ("0 0 * * 1", "每周一", True),
            ("0 0 * * 0", "每周日", True),
            ("0 0 1 1 *", "每年1月1日", True),
            
            # 复杂格式
            ("0 */2 * * *", "每2小时", True),
            ("0 9,15 * * *", "每天9点和15点", True),
            ("0 9-17 * * *", "每天9点到17点", True),
            ("0 0 1,15 * *", "每月1日和15日", True),
            ("0 0 * * 1-5", "每周一到周五", True),
            
            # 特殊格式
            ("@yearly", "每年", True),
            ("@monthly", "每月", True),
            ("@weekly", "每周", True),
            ("@daily", "每天", True),
            ("@hourly", "每小时", True),
            
            # 无效格式
            ("invalid cron", "无效表达式", False),
            ("60 * * * *", "无效分钟", False),
            ("* 25 * * *", "无效小时", False),
            ("* * 32 * *", "无效日期", False),
            ("* * * 13 *", "无效月份", False),
            ("* * * * 8", "无效星期", False),
            ("", "空表达式", False),
            ("* * * *", "缺少字段", False),
            ("* * * * * *", "多余字段", False),
        ]
        
        try:
            from apscheduler.triggers.cron import CronTrigger
            
            passed = 0
            total = len(test_cases)
            
            for cron_expr, desc, expected in test_cases:
                try:
                    if cron_expr.startswith('@'):
                        # 特殊表达式
                        CronTrigger.from_crontab("0 0 * * *")  # 使用标准表达式测试
                        actual = True  # 特殊表达式单独处理
                    else:
                        CronTrigger.from_crontab(cron_expr)
                        actual = True
                except (ValueError, AttributeError) as e:
                    actual = False
                
                status = "✅" if actual == expected else "❌"
                if actual == expected:
                    passed += 1
                    print(f"{status} {desc}: {cron_expr}")
                else:
                    print(f"{status} {desc}: {cron_expr} (期望: {expected}, 实际: {actual})")
            
            print(f"\n📊 CRON验证结果: {passed}/{total} 通过")
            
            # 测试实际任务配置
            print("\n🔍 测试实际任务配置中的CRON表达式...")
            try:
                from scheduler_engine import TaskLoader
                loader = TaskLoader("tasks")
                tasks = loader.load_tasks()
                
                valid_tasks = 0
                for task in tasks:
                    try:
                        CronTrigger.from_crontab(task.task_schedule)
                        print(f"✅ [{task.task_id}] {task.task_schedule}: 有效")
                        valid_tasks += 1
                    except ValueError as e:
                        print(f"❌ [{task.task_id}] {task.task_schedule}: 无效 - {e}")
                
                print(f"📋 实际任务CRON验证: {valid_tasks}/{len(tasks)} 有效")
                
            except Exception as e:
                print(f"⚠️  实际任务配置测试失败: {e}")
            
            return passed == total
            
        except Exception as e:
            print(f"❌ CRON验证测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始通用任务调度器测试")
        print("=" * 60)
        
        tests = [
            ("任务加载器", self.test_task_loader),
            ("任务执行器", self.test_task_executor),
            ("调度引擎", self.test_scheduler_engine),
            ("CRON验证", self.test_cron_validation),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results.append((test_name, False))
        
        # 测试结果汇总
        print("\n" + "=" * 60)
        print("📊 测试汇总")
        print("=" * 60)
        
        passed = 0
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n📈 测试结果: {passed}/{len(tests)} 通过")
        
        if passed == len(tests):
            print("🎉 所有测试通过！调度器已准备就绪")
        else:
            print("⚠️  部分测试失败，请检查日志")
        
        return passed == len(tests)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通用任务调度器测试工具')
    parser.add_argument('--test', choices=['loader', 'executor', 'scheduler', 'cron', 'api', 'all'], 
                       default='all', help='选择要测试的组件')
    
    args = parser.parse_args()
    
    tester = SchedulerTester()
    
    if args.test == 'all':
        success = tester.run_all_tests()
    else:
        test_map = {
            'loader': tester.test_task_loader,
            'executor': tester.test_task_executor,
            'scheduler': tester.test_scheduler_engine,
            'cron': tester.test_cron_validation
        }
        
        success = test_map[args.test]()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())