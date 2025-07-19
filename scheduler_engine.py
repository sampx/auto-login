#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用任务调度引擎
基于设计文档实现的完整任务调度系统
"""

import os
import json
import subprocess
import logging
import signal
import sys
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from logger_helper import LoggerHelper
import threading

@dataclass
class Task:
    """任务模型类"""
    task_id: str
    task_name: str
    task_exec: str
    task_schedule: str
    task_desc: str = ""
    task_timeout: Optional[int] = None
    task_retry: int = 0
    task_retry_interval: int = 60
    task_enabled: bool = True
    task_log: str = ""
    task_env: Optional[Dict[str, str]] = None
    task_dependencies: Optional[List[str]] = None
    task_notify: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.task_env is None:
            self.task_env = {}
        if self.task_dependencies is None:
            self.task_dependencies = []
        if self.task_notify is None:
            self.task_notify = {"on_success": False, "on_failure": False}
        if not self.task_log:
            self.task_log = f"logs/task_{self.task_id}.log"

    def has_critical_changes(self, other: 'Task') -> bool:
        """检测关键字段是否变更(影响调度计划的字段)"""
        return (self.task_enabled != other.task_enabled or
                self.task_schedule != other.task_schedule or
                self.task_exec != other.task_exec)

@dataclass
class TaskExecution:
    """任务执行记录模型"""
    task_id: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    return_code: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    duration: Optional[float] = None

class TaskLoader:
    """任务加载器"""
    
    def __init__(self, config_file: str = "tasks/config.json"):
        self.logger = LoggerHelper.get_system_logger("TaskLoader")
        self.config_file = config_file
        
    def load_tasks(self) -> List[Task]:
        """从配置文件加载所有任务"""
        if not os.path.exists(self.config_file):
            self.logger.info(f"配置文件 {self.config_file} 不存在，创建默认配置")
            self._create_default_config()
            return []
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            tasks = []
            if isinstance(data, list):
                # 直接任务列表格式
                task_list = data
            elif isinstance(data, dict) and 'tasks' in data:
                # 字典格式，包含tasks键
                task_list = data['tasks']
            else:
                self.logger.error("配置文件格式错误，应为任务列表或包含tasks键的字典")
                return []
                
            for task_data in task_list:
                try:
                    task = Task(**task_data)
                    if self._validate_task(task):
                        tasks.append(task)
                    else:
                        self.logger.warning(f"任务 {task.task_id} 验证失败，已跳过")
                except Exception as e:
                    self.logger.error(f"加载任务失败: {e}")
                    
            return tasks
            
        except Exception as e:
            self.logger.error(f"加载任务配置失败: {e}")
            return []
    
    def save_tasks(self, tasks: List[Task]):
        """保存任务到配置文件"""
        try:
            data = {
                "tasks": [asdict(task) for task in tasks]
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"已保存 {len(tasks)} 个任务到配置文件")
        except Exception as e:
            self.logger.error(f"保存任务配置失败: {e}")
    
    def _validate_task(self, task: Task) -> bool:
        """验证任务配置"""
        if not task.task_id or not task.task_name:
            return False
        # 不检查文件存在，因为是命令行执行
        if not task.task_exec:
            self.logger.warning("任务执行命令不能为空")
            return False
        return True
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_tasks = {
            "tasks": [
                {
                    "task_id": "test-task",
                    "task_name": "测试任务",
                    "task_desc": "用于测试任务调度引擎的功能",
                    "task_exec": "tasks/test_task.py",
                    "task_schedule": "*/5 * * * *",
                    "task_timeout": 300,
                    "task_retry": 2,
                    "task_retry_interval": 60,
                    "task_enabled": True,
                    "task_log": "logs/task_test-task.log",
                    "task_env": {
                        "TASK_NAME": "测试任务",
                        "TASK_DESCRIPTION": "通用任务调度引擎测试",
                        "PARAM1": "值1",
                        "PARAM2": "值2"
                    },
                    "task_dependencies": [],
                    "task_notify": {
                        "on_success": False,
                        "on_failure": True
                    }
                }
            ]
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_tasks, f, indent=2, ensure_ascii=False)
            self.logger.info(f"已创建默认配置文件: {self.config_file}")
        except Exception as e:
            self.logger.error(f"创建默认配置失败: {e}")

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.logger = LoggerHelper.get_system_logger("TaskExecutor")
        self.running_processes = {}
    
    def execute_task(self, task: Task) -> TaskExecution:
        """执行单个任务"""
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(
            task_id=task.task_id,
            execution_id=execution_id,
            start_time=datetime.now()
        )
        
        self.logger.info(f"开始执行任务 {task.task_id} (执行ID: {execution_id})")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update((task.task_env or {}).items())
            env['TASK_ID'] = task.task_id
            env['TASK_LOG'] = task.task_log
            
            # 确保日志目录存在
            os.makedirs(os.path.dirname(task.task_log), exist_ok=True)
            
            # 执行命令 - 支持shell命令和脚本
            cmd = task.task_exec.strip()
            
            # 检查是否为Python脚本文件
            if cmd.startswith('python ') and cmd.endswith('.py'):
                # Python脚本命令
                parts = cmd.split(' ', 1)
                script_path = parts[1]
                cmd = [sys.executable, script_path]
                shell = False
            elif cmd.endswith('.py') and ' ' not in cmd:
                # 单独Python脚本文件
                cmd = [sys.executable, cmd]
                shell = False
            else:
                # Shell命令或其他类型
                shell = True
            
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=shell
            )
            
            self.running_processes[execution_id] = process
            
            try:
                # 等待进程完成
                stdout, stderr = process.communicate(timeout=task.task_timeout)
                
                execution.end_time = datetime.now()
                execution.duration = (execution.end_time - execution.start_time).total_seconds()
                execution.return_code = process.returncode
                execution.output = stdout
                execution.error = stderr
                
                if process.returncode == 0:
                    execution.status = "success"
                    self.logger.info(f"任务 {task.task_id} 执行成功 (耗时: {execution.duration:.2f}s)")
                else:
                    execution.status = "failed"
                    execution.error_message = stderr or f"返回码: {process.returncode}"
                    self.logger.error(f"任务 {task.task_id} 执行失败 (返回码: {process.returncode})")
                    
            except subprocess.TimeoutExpired:
                process.kill()
                execution.end_time = datetime.now()
                execution.duration = (execution.end_time - execution.start_time).total_seconds()
                execution.status = "failed"
                execution.error_message = f"任务超时 (超过 {task.task_timeout} 秒)"
                self.logger.error(f"任务 {task.task_id} 执行超时")
                
        except Exception as e:
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.status = "failed"
            execution.error_message = str(e)
            self.logger.error(f"任务 {task.task_id} 执行异常: {e}")
            
        finally:
            if execution_id in self.running_processes:
                del self.running_processes[execution_id]
                
        return execution
    
    def stop_task(self, execution_id: str) -> bool:
        """停止正在执行的任务"""
        if execution_id in self.running_processes:
            process = self.running_processes[execution_id]
            try:
                process.terminate()
                process.wait(timeout=5)
                self.logger.info(f"已停止任务执行 {execution_id}")
                return True
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"强制停止任务执行 {execution_id}")
                return True
        return False

class SchedulerEngine:
    """任务调度引擎"""
    
    def __init__(self):
        self.logger = LoggerHelper.get_system_logger("SchedulerEngine")
        self.task_loader = TaskLoader()
        self.task_executor = TaskExecutor()
        self.scheduler = BackgroundScheduler()
        self.tasks = {}
        self.executions = {}
        
    def start(self):
        """启动调度引擎"""
        self.logger.info("启动通用任务调度引擎...")
        
        # 加载任务
        tasks = self.task_loader.load_tasks()
        self.logger.info(f"加载了 {len(tasks)} 个任务")
        
        # 添加任务到调度器
        for task in tasks:
            if task.task_enabled:
                self._add_task_to_scheduler(task)
            self.tasks[task.task_id] = task
        
        # 启动调度器
        self.scheduler.start()
        self.logger.info("任务调度引擎启动完成")
    
    def stop(self):
        """停止调度引擎"""
        self.logger.info("停止任务调度引擎...")
        self.scheduler.shutdown()
        self.logger.info("任务调度引擎已停止")
    
    def _add_task_to_scheduler(self, task: Task):
        """添加任务到调度器"""
        try:
            trigger = CronTrigger.from_crontab(task.task_schedule)
            
            self.scheduler.add_job(
                func=self._execute_task_wrapper,
                trigger=trigger,
                id=task.task_id,
                args=[task],
                max_instances=1,
                coalesce=True
            )
            
            self.logger.info(f"已添加任务 {task.task_id} 到调度器")
            
        except Exception as e:
            self.logger.error(f"添加任务 {task.task_id} 失败: {e}")
    
    def _execute_task_wrapper(self, task: Task):
        """任务执行包装器"""
        self.logger.info(f"开始调度执行任务 {task.task_id}")
        
        # 重试逻辑
        for attempt in range(task.task_retry + 1):
            execution = self.task_executor.execute_task(task)
            
            # 保存执行记录
            if task.task_id not in self.executions:
                self.executions[task.task_id] = []
            self.executions[task.task_id].append(execution)
            
            # 检查是否需要重试
            if execution.status == "success" or attempt >= task.task_retry:
                break
                
            self.logger.warning(f"任务 {task.task_id} 第 {attempt + 1} 次执行失败，准备重试...")
            time.sleep(task.task_retry_interval)
    
    def add_task(self, task: Task) -> bool:
        """添加新任务"""
        try:
            if task.task_id in self.tasks:
                self.logger.warning(f"任务 {task.task_id} 已存在")
                return False
                
            self.tasks[task.task_id] = task
            
            if task.task_enabled:
                self._add_task_to_scheduler(task)
                
            # 保存到配置文件
            all_tasks = list(self.tasks.values())
            self.task_loader.save_tasks(all_tasks)
            
            self.logger.info(f"已添加任务 {task.task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        try:
            if task_id not in self.tasks:
                return False
                
            # 从调度器移除
            if self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
                
            # 从内存移除
            del self.tasks[task_id]
            
            # 保存到配置文件
            all_tasks = list(self.tasks.values())
            self.task_loader.save_tasks(all_tasks)
            
            self.logger.info(f"已移除任务 {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除任务失败: {e}")
            return False
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        result = []
        for task in self.tasks.values():
            job = self.scheduler.get_job(task.task_id)
            next_run_time = job.next_run_time if job else None
            
            task_dict = asdict(task)
            task_dict['next_run_time'] = next_run_time.isoformat() if next_run_time else None
            
            result.append(task_dict)
        return result
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        if task_id not in self.tasks:
            return None
            
        task = self.tasks[task_id]
        job = self.scheduler.get_job(task_id)
        
        return {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_desc": task.task_desc,
            "task_exec": task.task_exec,
            "task_schedule": task.task_schedule,
            "task_timeout": task.task_timeout,
            "task_retry": task.task_retry,
            "task_retry_interval": task.task_retry_interval,
            "task_enabled": task.task_enabled,
            "task_log": task.task_log,
            "task_env": task.task_env,
            "task_dependencies": task.task_dependencies,
            "task_notify": task.task_notify,
            "next_run_time": job.next_run_time.isoformat() if job else None
        }
    
    def update_task(self, task: Task) -> bool:
        """更新任务"""
        try:
            if task.task_id not in self.tasks:
                return False

            # 获取原始任务进行比较
            original_task = self.tasks[task.task_id]
            if task == original_task:
                self.logger.info(f"任务 {task.task_id} 无变更，跳过更新")
                return True
                
            # 先移除旧的任务
            if self.scheduler.get_job(task.task_id):
                self.scheduler.remove_job(task.task_id)
                
            # 更新内存中的任务
            self.tasks[task.task_id] = task
            
            # 如果任务启用，重新添加到调度器
            if task.task_enabled:
                self._add_task_to_scheduler(task)
            
            # 保存到配置文件并验证
            all_tasks = list(self.tasks.values())
            self.task_loader.save_tasks(all_tasks)
            
            # 添加日志验证配置是否更新
            try:
                with open(self.task_loader.config_file, 'r') as f:
                    config = json.load(f)
                    updated = any(t['task_id'] == task.task_id and 
                                t['task_enabled'] == task.task_enabled 
                                for t in config['tasks'])
                    if not updated:
                        self.logger.error(f"配置更新验证失败: {task.task_id}")
                        return False
            except Exception as e:
                self.logger.error(f"验证配置更新失败: {e}")
                return False
                
            self.logger.info(f"已更新任务 {task.task_id} 并验证配置")
            return True
            
        except Exception as e:
            self.logger.error(f"更新任务失败: {e}")
            return False

    def toggle_task(self, task_id: str, enabled: bool) -> bool:
        """启用/禁用任务"""
        if task_id not in self.tasks:
            self.logger.error(f"任务 {task_id} 不存在")
            return False
            
        task = self.tasks[task_id]
        
        # 如果状态没有变化，直接返回成功
        if task.task_enabled == enabled:
            self.logger.info(f"任务 {task_id} 状态未改变")
            return True
            
        # 更新任务状态
        task.task_enabled = enabled
        
        # 立即从调度器中移除任务（无论启用还是禁用）
        if self.scheduler.get_job(task_id):
            self.scheduler.remove_job(task_id)
            self.logger.info(f"已从调度器移除任务 {task_id}")
            
        # 如果是启用状态，重新添加到调度器
        if enabled:
            self._add_task_to_scheduler(task)
            self.logger.info(f"已重新添加任务 {task_id} 到调度器")
            
        # 强制保存配置
        all_tasks = list(self.tasks.values())
        try:
            self.task_loader.save_tasks(all_tasks)
            # 验证配置是否更新
            with open(self.task_loader.config_file, 'r') as f:
                config = json.load(f)
                if not any(t['task_id'] == task_id and t['task_enabled'] == enabled
                          for t in config['tasks']):
                    raise ValueError("配置更新验证失败")
            self.logger.info(f"任务 {task_id} 状态已更新为 {'启用' if enabled else '禁用'}")
            return True
        except Exception as e:
            self.logger.error(f"保存任务状态失败: {e}")
            return False

    def execute_task_manually(self, task_id: str) -> bool:
        """手动触发一个任务的执行，在后台线程中运行"""
        if task_id not in self.tasks:
            self.logger.error(f"手动执行失败：找不到任务 {task_id}")
            return False

        task = self.tasks[task_id]
        self.logger.info(f"收到手动执行请求，为任务 {task_id} 创建后台线程")

        # 在一个新线程中执行任务，以避免阻塞API调用
        thread = threading.Thread(target=self._execute_task_wrapper, args=(task,))
        thread.daemon = True  # 设置为守护线程，主程序退出时线程也会退出
        thread.start()
        
        self.logger.info(f"任务 {task_id} 的手动执行线程已启动")
        return True

def main():
    """主函数"""
    engine = SchedulerEngine()
    
    def signal_handler(signum, frame):
        print(f"\n收到信号 {signum}，正在停止调度引擎...")
        engine.stop()
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        engine.start()
        print("通用任务调度引擎已启动，按 Ctrl+C 停止...")
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在停止...")
        engine.stop()
    except Exception as e:
        print(f"启动失败: {e}")
        engine.stop()

if __name__ == "__main__":
    main()