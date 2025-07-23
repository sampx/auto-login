#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用任务调度API完整测试脚本
包含：启动API服务器 → 运行测试 → 关闭服务器
"""

import requests
import json
import time
import subprocess
import signal
import os
import sys

class SchedulerAPITest:
    def __init__(self, port=5002):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.server_process = None
        
    def start_server(self):
        """启动API服务器"""
        print("🚀 启动API服务器...")
        try:
            # 检查端口是否被占用
            try:
                requests.get(f"{self.base_url}/api/scheduler/tasks", timeout=2)
                print("⚠️  端口已被占用，尝试关闭现有进程...")
                os.system(f"pkill -f 'scheduler_api.py'")
                time.sleep(2)
            except requests.exceptions.RequestException:
                pass  # 端口未占用
            
            # 启动服务器
            self.server_process = subprocess.Popen([
                sys.executable, "scheduler_api.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务器启动
            max_wait = 10
            for i in range(max_wait):
                try:
                    response = requests.get(f"{self.base_url}/api/scheduler/tasks", timeout=2)
                    if response.status_code == 200:
                        print("✅ API服务器启动成功")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
                
            print("❌ API服务器启动失败")
            return False
            
        except Exception as e:
            print(f"❌ 启动服务器错误: {e}")
            return False
    
    def stop_server(self):
        """关闭API服务器"""
        print("🛑 关闭API服务器...")
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                
            # 确保所有相关进程被关闭
            os.system(f"pkill -f 'scheduler_api.py'")
            print("✅ API服务器已关闭")
            
        except Exception as e:
            print(f"❌ 关闭服务器错误: {e}")
    
    def test_endpoint(self, url, method='GET', data=None, description=""):
        """测试单个API端点"""
        try:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, timeout=10)
            
            success = response.status_code < 400
            result = response.json() if success else response.text
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {description} - {method} {url}")
            
            if not success:
                print(f"   状态码: {response.status_code}")
                print(f"   错误: {result}")
                
            return success, result
            
        except Exception as e:
            print(f"❌ {description} - {e}")
            return False, str(e)
    
    def run_all_tests(self):
        """运行所有API测试"""
        tests_passed = 0
        tests_total = 0
        
        print("\n" + "="*60)
        print("🧪 开始通用任务调度API测试")
        print("="*60)
        
        # 1. 获取所有任务
        tests_total += 1
        success, tasks = self.test_endpoint(
            f"{self.base_url}/api/scheduler/tasks",
            "GET", 
            description="获取所有任务列表"
        )
        if success:
            tests_passed += 1
            print(f"   📊 找到 {tasks.get('total', 0)} 个任务")
        
        # 2. 获取单个任务详情
        if success and tasks.get('data'):
            tests_total += 1
            task_id = tasks['data'][0]['task_id']
            success, detail = self.test_endpoint(
                f"{self.base_url}/api/scheduler/tasks/{task_id}",
                "GET",
                description=f"获取任务详情: {task_id}"
            )
            if success:
                tests_passed += 1
        
        # 3. 创建新任务
        new_task = {
            "task_id": "integration_test_task",
            "task_name": "集成测试任务",
            "task_exec": "python tasks/test_task.py --integration-test",
            "task_schedule": "0 */12 * * *",
            "task_desc": "集成测试创建的任务",
            "task_timeout": 120,
            "task_retry": 1,
            "task_retry_interval": 30
        }
        tests_total += 1
        success, created = self.test_endpoint(
            f"{self.base_url}/api/scheduler/tasks",
            "POST",
            new_task,
            description="创建新任务"
        )
        if success:
            tests_passed += 1
        
        # 4. 更新任务
        if success:
            updated_task = {
                **new_task,
                "task_name": "更新后的集成测试任务",
                "task_desc": "已更新的集成测试任务"
            }
            tests_total += 1
            success, updated = self.test_endpoint(
                f"{self.base_url}/api/scheduler/tasks/{new_task['task_id']}",
                "PUT",
                updated_task,
                description="更新任务"
            )
            if success:
                tests_passed += 1
        
        # 5. 验证CRON表达式
        tests_total += 1
        success, cron_result = self.test_endpoint(
            f"{self.base_url}/api/scheduler/validate-cron",
            "POST",
            {"cron": "0 9 * * 1-5"},
            description="验证CRON表达式"
        )
        if success:
            tests_passed += 1
            if cron_result.get('data', {}).get('valid'):
                print(f"   📅 下次执行时间: {cron_result['data']['next_run']}")
        
        # 6. 手动执行任务
        if success and 'integration_test_task' in [t.get('task_id') for t in tasks.get('data', [])]:
            tests_total += 1
            success, executed = self.test_endpoint(
                f"{self.base_url}/api/scheduler/tasks/integration_test_task/execute",
                "POST",
                description="手动执行任务"
            )
            if success:
                tests_passed += 1
        
        # 7. 获取任务日志
        if success:
            tests_total += 1
            success, logs = self.test_endpoint(
                f"{self.base_url}/api/scheduler/tasks/integration_test_task/logs",
                "GET",
                description="获取任务日志"
            )
            if success:
                tests_passed += 1
                log_count = len(logs.get('data', []))
                print(f"   📋 获取到 {log_count} 行日志")
        
        # 8. 删除任务
        tests_total += 1
        success, deleted = self.test_endpoint(
            f"{self.base_url}/api/scheduler/tasks/integration_test_task",
            "DELETE",
            description="删除任务"
        )
        if success:
            tests_passed += 1
        
        # 9. 最终验证
        tests_total += 1
        success, final_tasks = self.test_endpoint(
            f"{self.base_url}/api/scheduler/tasks",
            "GET",
            description="最终验证任务列表"
        )
        if success:
            tests_passed += 1
            # 验证创建的任务已被删除
            task_ids = [t.get('task_id') for t in final_tasks.get('data', [])]
            if 'integration_test_task' not in task_ids:
                print("   ✅ 测试任务已成功清理")
        
        # 测试结果汇总
        print("\n" + "="*60)
        print("📊 测试完成汇总")
        print("="*60)
        print(f"总测试数: {tests_total}")
        print(f"通过测试: {tests_passed}")
        print(f"失败测试: {tests_total - tests_passed}")
        print(f"成功率: {(tests_passed/tests_total*100):.1f}%")
        
        if tests_passed == tests_total:
            print("🎉 所有测试通过！")
            return True
        else:
            print("❌ 部分测试失败")
            return False
    
    def run(self):
        """运行完整测试流程"""
        try:
            # 启动服务器
            if not self.start_server():
                return False
            
            # 等待服务器完全启动
            time.sleep(2)
            
            # 运行测试
            success = self.run_all_tests()
            
            return success
            
        except KeyboardInterrupt:
            print("\n🛑 测试被用户中断")
            return False
        except Exception as e:
            print(f"❌ 测试过程发生错误: {e}")
            return False
        finally:
            # 确保服务器被关闭
            self.stop_server()

def main():
    """主函数"""
    test_suite = SchedulerAPITest()
    
    try:
        success = test_suite.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()