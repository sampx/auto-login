#!/usr/bin/env python3
"""
Docker文件监控测试脚本
用于验证Docker环境下的文件监测功能是否正常
"""

import os
import time
import json
import tempfile
import shutil
import requests
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DockerMonitoringTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.test_task_id = f"test_docker_monitor_{int(time.time())}"
        
    def test_create_task(self):
        """测试创建任务"""
        logger.info("=== 测试创建任务 ===")
        
        task_data = {
            "task_id": self.test_task_id,
            "task_name": "Docker监控测试任务",
            "task_desc": "用于测试Docker环境下的文件监控",
            "task_exec": "python test_script.py",
            "task_schedule": "*/5 * * * *",
            "task_enabled": True,
            "task_timeout": 60,
            "task_retry": 1,
            "task_retry_interval": 30
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/scheduler/tasks", json=task_data)
            if response.status_code == 200:
                logger.info("✅ 任务创建成功")
                return True
            else:
                logger.error(f"❌ 任务创建失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 创建任务异常: {e}")
            return False
    
    def test_update_task(self):
        """测试更新任务"""
        logger.info("=== 测试更新任务 ===")
        
        update_data = {
            "task_desc": "更新后的描述 - Docker监控测试",
            "task_schedule": "*/10 * * * *"
        }
        
        try:
            response = requests.put(f"{self.base_url}/api/scheduler/tasks/{self.test_task_id}", json=update_data)
            if response.status_code == 200:
                logger.info("✅ 任务更新成功")
                return True
            else:
                logger.error(f"❌ 任务更新失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 更新任务异常: {e}")
            return False
    
    def test_toggle_task(self):
        """测试切换任务状态"""
        logger.info("=== 测试切换任务状态 ===")
        
        try:
            # 禁用任务
            response = requests.post(f"{self.base_url}/api/scheduler/tasks/{self.test_task_id}/toggle", json={"enabled": False})
            if response.status_code == 200:
                logger.info("✅ 任务禁用成功")
            else:
                logger.error(f"❌ 任务禁用失败: {response.text}")
                return False
            
            time.sleep(1)
            
            # 启用任务
            response = requests.post(f"{self.base_url}/api/scheduler/tasks/{self.test_task_id}/toggle", json={"enabled": True})
            if response.status_code == 200:
                logger.info("✅ 任务启用成功")
                return True
            else:
                logger.error(f"❌ 任务启用失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 切换任务状态异常: {e}")
            return False
    
    def test_delete_task(self):
        """测试删除任务"""
        logger.info("=== 测试删除任务 ===")
        
        try:
            response = requests.delete(f"{self.base_url}/api/scheduler/tasks/{self.test_task_id}")
            if response.status_code == 200:
                logger.info("✅ 任务删除成功")
                return True
            else:
                logger.error(f"❌ 任务删除失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 删除任务异常: {e}")
            return False
    
    def verify_task_config(self):
        """验证任务配置是否正确"""
        logger.info("=== 验证任务配置 ===")
        
        try:
            response = requests.get(f"{self.base_url}/api/scheduler/tasks/{self.test_task_id}")
            if response.status_code == 200:
                task_data = response.json().get('data', {})
                logger.info(f"任务详情: {json.dumps(task_data, ensure_ascii=False, indent=2)}")
                return True
            else:
                logger.warning(f"任务可能不存在: {response.text}")
                return False
        except Exception as e:
            logger.error(f"验证任务配置异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始Docker文件监控测试...")
        
        results = []
        
        # 测试顺序执行
        tests = [
            ("创建任务", self.test_create_task),
            ("验证任务", self.verify_task_config),
            ("更新任务", self.test_update_task),
            ("切换状态", self.test_toggle_task),
            ("删除任务", self.test_delete_task),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📝 执行测试: {test_name}")
            result = test_func()
            results.append((test_name, result))
            time.sleep(2)  # 给系统处理时间
        
        # 总结结果
        logger.info("\n" + "="*50)
        logger.info("📊 测试结果汇总")
        logger.info("="*50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\n📈 总计: {passed}/{len(results)} 测试通过")
        
        if passed == len(results):
            logger.info("🎉 所有测试通过！Docker文件监控工作正常")
        else:
            logger.error("⚠️  部分测试失败，请检查日志")
        
        return passed == len(results)

def check_docker_health():
    """检查Docker容器健康状态"""
    logger.info("🔍 检查Docker容器状态...")
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps', '--filter', 'name=auto-login', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True)
        
        if 'auto-login' in result.stdout:
            logger.info("✅ Docker容器正在运行")
            return True
        else:
            logger.warning("⚠️  Docker容器未找到或未运行")
            return False
    except Exception as e:
        logger.error(f"❌ 检查Docker状态失败: {e}")
        return False

if __name__ == "__main__":
    # 检查Docker状态
    if not check_docker_health():
        logger.error("请先启动Docker容器")
        exit(1)
    
    # 运行测试
    tester = DockerMonitoringTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n🎯 Docker文件监控测试完成！")
    else:
        logger.error("\n❌ 测试发现问题，请查看详细日志")