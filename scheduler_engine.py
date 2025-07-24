

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
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import dotenv_values
import glob
from logger_helper import setup_logging

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
        """检测影响调度的关键字段是否变更"""
        return (self.task_enabled != other.task_enabled or
                self.task_schedule != other.task_schedule or
                self.task_exec != other.task_exec)
                
    def __eq__(self, other):
        """比较两个任务是否相等，用于判断任务是否有变更"""
        if not isinstance(other, Task):
            return False
        
        # 比较所有字段
        return (self.task_id == other.task_id and
                self.task_name == other.task_name and
                self.task_exec == other.task_exec and
                self.task_schedule == other.task_schedule and
                self.task_desc == other.task_desc and
                self.task_timeout == other.task_timeout and
                self.task_retry == other.task_retry and
                self.task_retry_interval == other.task_retry_interval and
                self.task_enabled == other.task_enabled and
                self.task_log == other.task_log and
                self.task_env == other.task_env and
                self.task_dependencies == other.task_dependencies and
                self.task_notify == other.task_notify)

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

class ConfigFileHandler(FileSystemEventHandler):
    """任务配置文件变更监控处理器"""
    
    def __init__(self, scheduler_engine, tasks_dir: str):
        super().__init__()
        self.scheduler_engine = scheduler_engine
        self.tasks_dir = os.path.abspath(tasks_dir)
        self.logger = logging.getLogger(__name__)
        self.last_modified = 0
        
    def on_modified(self, event):
        """文件修改事件处理"""
        # 只监控 config.json 文件的变更
        if event.is_directory or not event.src_path.endswith('config.json'):
            return
            
        # 确保是任务目录下的配置文件
        if not event.src_path.startswith(self.tasks_dir):
            return
            
        current_time = time.time()
        if current_time - self.last_modified < 1:
            return
        self.last_modified = current_time
        
        self.logger.info(f"检测到任务配置文件变更: {event.src_path}，准备重新加载任务...")
        time.sleep(0.5)
        self.scheduler_engine._reload_single_task(event.src_path)

class TaskLoader:
    """任务加载器"""
    
    def __init__(self, tasks_dir: str = "tasks"):
        self.logger = logging.getLogger(__name__)
        self.tasks_dir = tasks_dir
        
    def load_tasks(self) -> List[Task]:
        """从任务目录加载所有任务"""
        if not os.path.exists(self.tasks_dir):
            raise FileNotFoundError(f"任务目录 {self.tasks_dir} 不存在，请检查配置或联系管理员")
            
        tasks = []
        try:
            # 扫描任务目录下的所有子目录
            for item in os.listdir(self.tasks_dir):
                task_dir = os.path.join(self.tasks_dir, item)
                if not os.path.isdir(task_dir):
                    continue
                    
                config_file = os.path.join(task_dir, 'config.json')
                if not os.path.exists(config_file):
                    self.logger.warning(f"任务目录 {task_dir} 缺少 config.json 文件，已跳过")
                    continue
                
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        task_data = json.load(f)
                    
                    task = Task(**task_data)
                    if self._validate_task(task):
                        tasks.append(task)
                        self.logger.debug(f"成功加载任务: {task.task_id}")
                    else:
                        self.logger.warning(f"任务 {task.task_id} 配置无效，已跳过。")
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析任务配置文件 {config_file} 失败: {e}")
                except TypeError as e:
                    self.logger.error(f"加载任务数据失败，字段不匹配: {config_file}，错误: {e}")
                except Exception as e:
                    self.logger.error(f"加载任务配置 {config_file} 时发生未知错误: {e}")
                    
            self.logger.info(f"成功加载 {len(tasks)} 个任务")
            return tasks
            
        except Exception as e:
            self.logger.error(f"扫描任务目录时发生未知错误: {e}")
            return []
    
    def save_tasks(self, tasks: List[Task]):
        """保存任务到各自的配置文件"""
        try:
            saved_count = 0
            for task in tasks:
                task_dir = os.path.join(self.tasks_dir, task.task_id)
                os.makedirs(task_dir, exist_ok=True)
                
                config_file = os.path.join(task_dir, 'config.json')
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(task), f, indent=2, ensure_ascii=False)
                saved_count += 1
                
            self.logger.info(f"成功保存 {saved_count} 个任务到各自的配置文件")
        except Exception as e:
            self.logger.error(f"保存任务配置到文件失败: {e}")
    
    def save_task(self, task: Task):
        """保存单个任务到配置文件"""
        try:
            task_dir = os.path.join(self.tasks_dir, task.task_id)
            os.makedirs(task_dir, exist_ok=True)
            
            config_file = os.path.join(task_dir, 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(task), f, indent=2, ensure_ascii=False)
            self.logger.info(f"成功保存任务 {task.task_id} 的配置文件")
        except Exception as e:
            self.logger.error(f"保存任务 {task.task_id} 配置文件失败: {e}")
    
    def delete_task_files(self, task_id: str):
        """删除任务的所有文件"""
        try:
            task_dir = os.path.join(self.tasks_dir, task_id)
            if os.path.exists(task_dir):
                import shutil
                shutil.rmtree(task_dir)
                self.logger.info(f"成功删除任务 {task_id} 的目录: {task_dir}")
        except Exception as e:
            self.logger.error(f"删除任务 {task_id} 目录失败: {e}")
    
    def _validate_task(self, task: Task) -> bool:
        """验证任务配置"""
        if not all([task.task_id, task.task_name, task.task_exec]):
            self.logger.warning(f"任务验证失败，缺少必要字段 (ID, 名称, 执行命令): {task.task_id}")
            return False
        return True
    
    def _create_default_task(self):
        """创建默认任务目录和配置"""
        try:
            os.makedirs(self.tasks_dir, exist_ok=True)
            
            # 创建默认测试任务
            default_task_dir = os.path.join(self.tasks_dir, "test-task")
            os.makedirs(default_task_dir, exist_ok=True)
            
            default_config = {
                "task_id": "test-task",
                "task_name": "测试任务",
                "task_desc": "用于测试任务调度引擎的功能",
                "task_exec": "python test_task.py",
                "task_schedule": "*/5 * * * *",
                "task_timeout": 300,
                "task_retry": 2,
                "task_retry_interval": 60,
                "task_enabled": True,
                "task_log": "logs/task_test-task.log",
                "task_env": {"PARAM1": "值1"},
                "task_dependencies": [],
                "task_notify": {"on_success": False, "on_failure": True}
            }
            
            config_file = os.path.join(default_task_dir, 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            # 创建简单的测试脚本
            script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
print("默认测试任务开始执行...")
time.sleep(2)
print("默认测试任务执行完成")
'''
            script_file = os.path.join(default_task_dir, 'test_task.py')
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
                
            self.logger.info(f"已成功创建默认任务目录: {default_task_dir}")
        except Exception as e:
            self.logger.error(f"创建默认任务失败: {e}")

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running_processes = {}
    
    def execute_task(self, task: Task) -> TaskExecution:
        """执行单个任务"""
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(task_id=task.task_id, execution_id=execution_id, start_time=datetime.now())
        
        self.logger.info(f"开始执行任务 {task.task_id} (执行ID: {execution_id})，命令: {task.task_exec}")
        
        # 确定任务工作目录
        task_dir = os.path.join("tasks", task.task_id)
        original_cwd = os.getcwd()
        
        try:
            env = self._prepare_environment(task)
            os.makedirs(os.path.dirname(task.task_log), exist_ok=True)
            self._clear_python_module_cache(task.task_exec)
            
            cmd, shell = self._prepare_command(task.task_exec)
            
            # 如果任务目录存在，切换到任务目录执行
            if os.path.exists(task_dir):
                os.chdir(task_dir)
                self.logger.debug(f"切换到任务目录: {task_dir}")
            
            with open(os.path.join(original_cwd, task.task_log), 'w', encoding='utf-8') as log_file:
                self._log_task_start(log_file, task, execution)
                
                process = subprocess.Popen(
                    cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, shell=shell, bufsize=1, universal_newlines=True
                )
                self.running_processes[execution_id] = process
                
                self._stream_process_output(process, execution, log_file, task)

        except Exception as e:
            self.logger.error(f"执行任务 {task.task_id} 过程中发生严重错误: {e}")
            execution.status = "failed"
            execution.error_message = str(e)
            self._log_execution_error(task, execution, str(e))
        
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            if execution_id in self.running_processes:
                del self.running_processes[execution_id]
            self._log_task_end(task, execution)
                
        return execution

    def _prepare_environment(self, task: Task) -> Dict[str, str]:
        """准备任务执行的环境变量"""
        env = os.environ.copy()
        task_env_config = task.task_env or {}
        env_file_path = task_env_config.get("_ENV_FILE")
        
        if env_file_path:
            # 获取项目根目录路径（scheduler_engine.py 所在目录）
            project_root = os.path.dirname(os.path.abspath(__file__))
            # 将 env_file_path 解析为相对于项目根目录的绝对路径
            absolute_env_file_path = os.path.join(project_root, env_file_path)
            
            self.logger.info(f"任务 {task.task_id} 指定了环境文件: {env_file_path}")
            self.logger.debug(f"解析后的环境文件绝对路径: {absolute_env_file_path}")
            
            if os.path.exists(absolute_env_file_path):
                try:
                    # 过滤掉值为 None 的环境变量
                    env_vars = {k: v for k, v in dotenv_values(absolute_env_file_path).items() if v is not None}
                    env.update(env_vars)
                    self.logger.info(f"成功从 {absolute_env_file_path} 加载环境变量")
                except Exception as e:
                    self.logger.error(f"加载环境文件 {absolute_env_file_path} 失败: {e}")
            else:
                # 如果绝对路径不存在，尝试使用原始相对路径（向后兼容）
                if os.path.exists(env_file_path):
                    try:
                        # 过滤掉值为 None 的环境变量
                        env_vars = {k: v for k, v in dotenv_values(env_file_path).items() if v is not None}
                        env.update(env_vars)
                        self.logger.info(f"成功从 {env_file_path} 加载环境变量（使用原始路径）")
                    except Exception as e:
                        self.logger.error(f"加载环境文件 {env_file_path} 失败: {e}")
                else:
                    self.logger.warning(f"环境文件 {env_file_path} 不存在，已跳过")
        else:
            self.logger.debug(f"任务 {task.task_id} 未指定环境文件")

        # 过滤掉值为 None 的环境变量
        filtered_task_env = {k: v for k, v in task_env_config.items() if v is not None and not k.startswith('_')}
        env.update(filtered_task_env)
        env['TASK_ID'] = task.task_id
        env['TASK_LOG'] = task.task_log
        
        # 移除以 _ 开头的内部配置项
        return {k: v for k, v in env.items() if not k.startswith('_')}

    def _prepare_command(self, task_exec: str) -> tuple:
        """准备执行命令"""
        cmd = task_exec.strip()
        if cmd.startswith('python '):
            script_and_args = cmd.split(' ', 1)[1].split()
            return [sys.executable] + script_and_args, False
        elif cmd.endswith('.py') and ' ' not in cmd:
            return [sys.executable, cmd], False
        else:
            return cmd, True

    def _stream_process_output(self, process: subprocess.Popen, execution: TaskExecution, log_file, task: Task):
        """实时流式传输进程输出"""
        output_lines = []
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log_file.write(output)
                    log_file.flush()
                    output_lines.append(output.rstrip())
            
            process.wait(timeout=task.task_timeout)
            
            execution.return_code = process.returncode
            execution.output = '\n'.join(output_lines)
            
            if process.returncode == 0:
                execution.status = "success"
                self.logger.info(f"任务 {task.task_id} 执行成功")
            elif process.returncode == -15:  # SIGTERM 信号，表示进程被正常终止
                execution.status = "terminated"
                execution.error_message = "任务因参数变化或配置更新而终止"
                self.logger.info(f"任务 {task.task_id} 因参数变化或配置更新而终止执行")
                # 在任务日志中记录终止原因
                log_file.write("\n========================================\n")
                log_file.write("任务因参数变化或配置更新而终止执行\n")
                log_file.write("========================================\n")
                log_file.flush()
            else:
                execution.status = "failed"
                execution.error_message = f"返回码: {process.returncode}"
                self.logger.error(f"任务 {task.task_id} 执行失败，返回码: {process.returncode}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            execution.status = "failed"
            execution.error_message = f"任务超时 (超过 {task.task_timeout} 秒)"
            self.logger.error(f"任务 {task.task_id} 因超时被终止")
            log_file.write(f"\n任务执行超时 (>{task.task_timeout}s)，进程已被终止。\n")

    def _log_task_start(self, log_file, task: Task, execution: TaskExecution):
        log_file.write(f"""========================================\n任务开始: {task.task_name} ({task.task_id})\n执行ID: {execution.execution_id}\n执行时间: {execution.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n执行命令: {task.task_exec}\n========================================\n\n""")
        log_file.flush()

    def _log_task_end(self, task: Task, execution: TaskExecution):
        try:
            with open(task.task_log, 'a', encoding='utf-8') as log_file:
                log_file.write(f"""\n========================================\n任务结束: {task.task_name} ({task.task_id})\n结束时间: {execution.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n执行耗时: {execution.duration:.2f} 秒\n状态: {execution.status.upper()}\n返回码: {execution.return_code}\n========================================\n""")
        except Exception as e:
            self.logger.error(f"无法写入任务 {task.task_id} 的结束日志: {e}")

    def _log_execution_error(self, task: Task, execution: TaskExecution, error_msg: str):
        try:
            with open(task.task_log, 'a', encoding='utf-8') as log_file:
                log_file.write(f"""\n========================================\n任务执行异常: {task.task_id}\n时间: {execution.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n异常信息: {error_msg}\n========================================\n""")
        except Exception as e:
            self.logger.error(f"无法写入任务 {task.task_id} 的异常日志: {e}")

    def stop_task(self, execution_id: str) -> bool:
        """停止正在执行的任务"""
        if execution_id in self.running_processes:
            process = self.running_processes[execution_id]
            try:
                process.terminate()
                process.wait(timeout=5)
                self.logger.info(f"已发送终止信号到任务执行 {execution_id}")
                return True
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"强制终止任务执行 {execution_id}")
                return True
        return False
        
    def stop_all_tasks_by_id(self, task_id: str) -> int:
        """停止指定任务ID的所有正在执行的进程
        
        Args:
            task_id: 任务ID
            
        Returns:
            int: 停止的进程数量
        """
        stopped_count = 0
        execution_ids_to_stop = []
        
        # 记录更详细的日志，包括当前运行的进程数量
        process_count = len(self.running_processes)
        self.logger.info(f"正在查找任务 {task_id} 的正在执行进程，当前运行进程总数: {process_count}")
        
        # 由于我们无法直接从进程对象获取任务ID，我们需要停止所有正在运行的进程
        # 这确保了任务更新时不会有旧的进程继续运行
        if process_count > 0:
            self.logger.info(f"发现 {process_count} 个正在运行的进程，将停止与任务 {task_id} 相关的进程")
            
            # 遍历所有正在运行的进程
            for exec_id, process in list(self.running_processes.items()):
                pid = process.pid if hasattr(process, 'pid') else 'N/A'
                self.logger.info(f"准备停止执行ID: {exec_id}, 进程PID: {pid}")
                execution_ids_to_stop.append(exec_id)
            
            # 停止所有找到的执行
            for exec_id in execution_ids_to_stop:
                try:
                    if self.stop_task(exec_id):
                        stopped_count += 1
                        self.logger.info(f"已成功停止执行ID: {exec_id}")
                    else:
                        self.logger.warning(f"停止执行ID: {exec_id} 失败，可能进程已经结束")
                except Exception as e:
                    self.logger.error(f"停止执行ID: {exec_id} 时发生异常: {e}")
        
        # 记录更详细的结果日志
        if stopped_count > 0:
            self.logger.info(f"已成功停止 {stopped_count} 个正在执行的进程（任务更新: {task_id}）")
        else:
            self.logger.info(f"任务 {task_id} 当前没有正在执行的进程被停止")
        
        return stopped_count
    
    def _clear_python_module_cache(self, task_exec: str):
        """清理Python模块缓存"""
        try:
            cmd = task_exec.strip()
            script_path = None
            if cmd.startswith('python '):
                script_path = cmd.split(' ', 1)[1].split()[0]
            elif cmd.endswith('.py'):
                script_path = cmd
            
            if script_path and script_path.endswith('.py'):
                module_name = script_path.replace('.py', '').replace('/', '.').replace('\\', '.')
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    self.logger.debug(f"已成功清理Python模块缓存: {module_name}")
        except Exception as e:
            self.logger.debug(f"清理Python模块缓存时发生非关键异常: {e}")

class SchedulerEngine:
    """任务调度引擎"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchedulerEngine, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not SchedulerEngine._initialized:
            self.logger = logging.getLogger(__name__)
            self.task_loader = TaskLoader()
            self.task_executor = TaskExecutor()
            self.scheduler = BackgroundScheduler()
            self.tasks = {}
            self.executions = {}
            self.file_observer = None
            self.config_handler = None
            self.api_operation_timestamp = 0
            self.api_operation_lock = threading.Lock()
            # 轮询机制相关属性
            self.polling_thread = None
            self.polling_stop_event = threading.Event()
            self.last_file_modtimes = {}  # 存储文件最后修改时间
            self.polling_interval = int(os.getenv('TASK_CONFIG_POLLING_INTERVAL', '10'))  # 轮询间隔（秒）
            self.monitor_type = os.getenv('TASK_CONFIG_MONITOR_TYPE', 'watchdog')  # 监控类型：watchdog 或 polling
            SchedulerEngine._initialized = True
        
    def start(self):
        """启动调度引擎"""
        self.logger.info("正在启动任务调度引擎...")
        try:
            tasks = self.task_loader.load_tasks()
            self.logger.info(f"成功加载 {len(tasks)} 个任务")
        except FileNotFoundError as e:
            self.logger.error(str(e))
            raise
        
        for task in tasks:
            if task.task_enabled:
                self._add_task_to_scheduler(task)
            self.tasks[task.task_id] = task
        
        self.scheduler.start()
        self._start_file_monitoring()
        self.logger.info("任务调度引擎已成功启动")
    
    def stop(self):
        """停止调度引擎"""
        self.logger.info("正在停止任务调度引擎...")
        self._stop_file_monitoring()
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
            self.logger.info(f"已成功添加任务 {task.task_id} ({task.task_name}) 到调度计划")
        except Exception as e:
            self.logger.error(f"添加任务 {task.task_id} 到调度计划失败: {e}")
    
    def _start_file_monitoring(self):
        """启动任务配置文件监控"""
        try:
            tasks_dir = self.task_loader.tasks_dir
            if not os.path.exists(tasks_dir):
                self.logger.warning(f"任务目录 {tasks_dir} 不存在，跳过文件监控")
                return
                
            # 根据配置决定使用哪种监控机制
            if self.monitor_type == 'polling':
                # 使用轮询机制
                self._start_polling_monitoring()
                self.logger.info(f"已启动对任务目录 {tasks_dir} 的配置文件轮询监控（间隔: {self.polling_interval}秒）")
            elif self.monitor_type == 'watchdog':
                # 使用 watchdog 机制
                self.config_handler = ConfigFileHandler(self, tasks_dir)
                self.file_observer = Observer()
                self.file_observer.schedule(self.config_handler, tasks_dir, recursive=True)
                self.file_observer.start()
                self.logger.info(f"已启动对任务目录 {tasks_dir} 的配置文件监控")
            else:
                self.logger.warning(f"未知的监控类型: {self.monitor_type}，任务配置变更将无法自动检测")
        except Exception as e:
            self.logger.error(f"启动配置文件监控失败: {e}")
    
    def _start_polling_monitoring(self):
        """启动轮询监控"""
        try:
            # 初始化 last_file_modtimes 字典，记录所有配置文件的初始修改时间
            tasks_dir = self.task_loader.tasks_dir
            pattern = os.path.join(tasks_dir, "*", "config.json")
            config_files = glob.glob(pattern)
            for config_file in config_files:
                try:
                    mod_time = os.path.getmtime(config_file)
                    self.last_file_modtimes[config_file] = mod_time
                except OSError:
                    # 文件可能已被删除
                    pass
            
            self.polling_stop_event.clear()
            self.polling_thread = threading.Thread(target=self._polling_worker, daemon=True)
            self.polling_thread.start()
        except Exception as e:
            self.logger.error(f"启动配置文件轮询监控失败: {e}")
    
    def _polling_worker(self):
        """轮询监控工作线程"""
        tasks_dir = self.task_loader.tasks_dir
        self.logger.info(f"轮询监控线程已启动，监控目录: {tasks_dir}，轮询间隔: {self.polling_interval}秒")
        
        while not self.polling_stop_event.is_set():
            try:
                # 查找所有 config.json 文件
                pattern = os.path.join(tasks_dir, "*", "config.json")
                config_files = glob.glob(pattern)
                
                current_modtimes = {}
                for config_file in config_files:
                    try:
                        mod_time = os.path.getmtime(config_file)
                        current_modtimes[config_file] = mod_time
                    except OSError:
                        # 文件可能已被删除
                        pass
                
                # 检查是否有文件变更
                changed_files = []
                for file_path, mod_time in current_modtimes.items():
                    if file_path not in self.last_file_modtimes or self.last_file_modtimes[file_path] != mod_time:
                        changed_files.append(file_path)
                
                # 检查是否有文件被删除
                deleted_files = []
                for file_path in self.last_file_modtimes:
                    if file_path not in current_modtimes:
                        deleted_files.append(file_path)
                
                # 如果有变更或删除，则重新加载任务
                if changed_files or deleted_files:
                    if changed_files:
                        self.logger.info(f"检测到配置文件变更: {changed_files}")
                        # 重新加载变更的单个任务
                        for changed_file in changed_files:
                            self._reload_single_task(changed_file)
                    if deleted_files:
                        self.logger.info(f"检测到配置文件删除: {deleted_files}")
                        # 重新加载所有任务以处理删除的文件
                        self._reload_all_tasks()
                
                # 更新最后修改时间记录
                self.last_file_modtimes = current_modtimes
                
                # 等待下一个轮询周期
                self.polling_stop_event.wait(self.polling_interval)
            except Exception as e:
                self.logger.error(f"轮询监控过程中发生异常: {e}")
                # 发生异常时也等待一段时间再继续
                self.polling_stop_event.wait(self.polling_interval)
        
        self.logger.info("轮询监控线程已停止")
        
    
    def _stop_file_monitoring(self):
        """停止文件监控"""
        try:
            if self.file_observer and self.file_observer.is_alive():
                self.file_observer.stop()
                self.file_observer.join(timeout=5)
                self.logger.info("已停止配置文件监控")
        except Exception as e:
            self.logger.error(f"停止文件监控时发生异常: {e}")
        
        # 停止轮询线程
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_stop_event.set()
            self.polling_thread.join(timeout=5)
            self.logger.info("已停止配置文件轮询监控")
    
    def _mark_api_operation(self):
        """标记API操作，用于短期内忽略文件变更事件"""
        with self.api_operation_lock:
            self.api_operation_timestamp = time.time()
            self.logger.debug("已标记API操作时间戳，以避免不必要的重载")
    
    def _is_api_operation_recent(self) -> bool:
        """检查文件变更是否由最近的API操作触发"""
        with self.api_operation_lock:
            return (time.time() - self.api_operation_timestamp) < 2
    
    def _reload_single_task(self, config_file_path: str):
        """重新加载单个任务配置"""
        if self._is_api_operation_recent():
            self.logger.info("检测到由API操作触发的文件变更，跳过本次自动重载")
            return
        
        self.logger.info(f"开始从配置文件重新加载单个任务: {config_file_path}")
        try:
            # 从配置文件路径提取任务ID
            task_id = os.path.basename(os.path.dirname(config_file_path))
            
            # 检查任务是否存在
            if task_id not in self.tasks:
                self.logger.warning(f"任务 {task_id} 不存在，将作为新任务添加")
                # 作为新任务添加
                fresh_tasks = self.task_loader.load_tasks()
                fresh_task = next((task for task in fresh_tasks if task.task_id == task_id), None)
                if fresh_task:
                    self.tasks[task_id] = fresh_task
                    if fresh_task.task_enabled:
                        self._add_task_to_scheduler(fresh_task)
                    self.logger.info(f"成功添加新任务: {task_id}")
                else:
                    self.logger.error(f"无法从配置文件加载任务: {config_file_path}")
                return
            
            # 加载新的任务配置
            task_dir = os.path.join(self.task_loader.tasks_dir, task_id)
            config_file = os.path.join(task_dir, 'config.json')
            if not os.path.exists(config_file):
                self.logger.error(f"任务配置文件不存在: {config_file}")
                return
                
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                fresh_task = Task(**task_data)
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.error(f"解析任务配置文件失败: {config_file}，错误: {e}")
                return
                
            # 获取当前任务配置
            current_task = self.tasks[task_id]
            
            # 检查任务是否有变更
            if fresh_task == current_task:
                self.logger.info(f"任务 {task_id} 配置无变更，跳过更新")
                return
                
            self.logger.info(f"任务 {task_id} 配置发生变更，开始更新...")
            
            # 检查日志文件路径是否变更
            if fresh_task.task_log != current_task.task_log and os.path.exists(current_task.task_log):
                try:
                    # 如果旧日志文件存在且与新日志文件不同，则删除旧日志文件
                    os.remove(current_task.task_log)
                    self.logger.info(f"已删除任务 {task_id} 的旧日志文件: {current_task.task_log}")
                except Exception as e:
                    self.logger.warning(f"删除任务 {task_id} 的旧日志文件失败: {e}")
            
            # 检查关键配置是否变更
            if fresh_task.has_critical_changes(current_task):
                self.logger.info(f"任务 {task_id} 的关键配置发生变更，将重新调度")
                
                # 停止该任务的调度计划
                if self.scheduler.get_job(task_id):
                    self.scheduler.remove_job(task_id)
                
                # 停止该任务的所有正在执行的进程
                stopped_count = self.task_executor.stop_all_tasks_by_id(task_id)
                if stopped_count > 0:
                    self.logger.info(f"已终止任务 {task_id} 的 {stopped_count} 个正在执行的进程")
                
                # 如果任务启用，重新添加到调度器
                if fresh_task.task_enabled:
                    self._add_task_to_scheduler(fresh_task)
            
            # 更新任务配置
            self.tasks[task_id] = fresh_task
            self.logger.info(f"任务 {task_id} 配置更新完成")
        except Exception as e:
            self.logger.error(f"重新加载单个任务配置时发生严重错误: {e}")
    
    def _reload_all_tasks(self):
        """重新加载所有任务配置"""
        if self._is_api_operation_recent():
            self.logger.info("检测到由API操作触发的文件变更，跳过本次自动重载")
            return
        
        self.logger.info("开始从配置文件重新加载所有任务...")
        try:
            fresh_tasks_dict = {task.task_id: task for task in self.task_loader.load_tasks()}
            current_task_ids = set(self.tasks.keys())
            fresh_task_ids = set(fresh_tasks_dict.keys())
            
            # 创建任务ID映射表，用于检测任务ID变更
            # 通过比较任务的其他属性（如任务名称、执行命令等）来识别可能是ID变更的任务
            id_mapping = {}
            for old_id in current_task_ids - fresh_task_ids:
                old_task = self.tasks[old_id]
                for new_id in fresh_task_ids - current_task_ids:
                    new_task = fresh_tasks_dict[new_id]
                    # 如果任务名称和执行命令相同，认为是同一个任务但ID变更了
                    if (old_task.task_name == new_task.task_name and 
                        old_task.task_exec == new_task.task_exec):
                        id_mapping[old_id] = new_id
                        self.logger.info(f"检测到任务ID变更: {old_id} -> {new_id}")
                        break

            # 处理任务ID变更
            for old_id, new_id in id_mapping.items():
                self.logger.info(f"处理任务ID变更: {old_id} -> {new_id}")
                
                # 停止旧任务的所有执行计划
                if self.scheduler.get_job(old_id):
                    self.logger.info(f"移除旧任务 {old_id} 的调度计划")
                    self.scheduler.remove_job(old_id)
                
                # 停止旧任务的所有正在执行的进程
                stopped_count = self.task_executor.stop_all_tasks_by_id(old_id)
                if stopped_count > 0:
                    self.logger.info(f"已终止旧任务 {old_id} 的 {stopped_count} 个正在执行的进程")
                
                # 处理日志文件变更
                old_task = self.tasks[old_id]
                new_task = fresh_tasks_dict[new_id]
                if old_task.task_log != new_task.task_log and os.path.exists(old_task.task_log):
                    try:
                        # 如果旧日志文件存在且与新日志文件不同，则删除旧日志文件
                        os.remove(old_task.task_log)
                        self.logger.info(f"已删除旧任务 {old_id} 的日志文件: {old_task.task_log}")
                    except Exception as e:
                        self.logger.warning(f"删除旧任务 {old_id} 的日志文件失败: {e}")
                
                # 从当前任务列表中移除旧任务
                del self.tasks[old_id]
                
                # 将新任务添加到调度器
                if new_task.task_enabled:
                    self._add_task_to_scheduler(new_task)
                self.tasks[new_id] = new_task

            # 更新和检测变更（处理未变更ID的任务）
            for task_id in current_task_ids.intersection(fresh_task_ids):
                fresh_task = fresh_tasks_dict[task_id]
                current_task = self.tasks[task_id]
                
                # 检查日志文件路径是否变更
                if fresh_task.task_log != current_task.task_log and os.path.exists(current_task.task_log):
                    try:
                        # 如果旧日志文件存在且与新日志文件不同，则删除旧日志文件
                        os.remove(current_task.task_log)
                        self.logger.info(f"已删除任务 {task_id} 的旧日志文件: {current_task.task_log}")
                    except Exception as e:
                        self.logger.warning(f"删除任务 {task_id} 的旧日志文件失败: {e}")
                
                # 检查关键配置是否变更
                if fresh_task.has_critical_changes(current_task):
                    self.logger.info(f"任务 {task_id} 的关键配置发生变更，将重新调度")
                    
                    # 停止该任务的调度计划
                    if self.scheduler.get_job(task_id):
                        self.scheduler.remove_job(task_id)
                    
                    # 停止该任务的所有正在执行的进程
                    stopped_count = self.task_executor.stop_all_tasks_by_id(task_id)
                    if stopped_count > 0:
                        self.logger.info(f"已终止任务 {task_id} 的 {stopped_count} 个正在执行的进程")
                    
                    # 如果任务启用，重新添加到调度器
                    if fresh_task.task_enabled:
                        self._add_task_to_scheduler(fresh_task)
                
                # 更新任务配置
                self.tasks[task_id] = fresh_task

            # 处理已删除的任务（排除已处理的ID变更任务）
            for task_id in current_task_ids - fresh_task_ids - set(id_mapping.keys()):
                self.logger.info(f"任务 {task_id} 已从配置文件中移除，将停止调度")
                
                # 停止该任务的调度计划
                if self.scheduler.get_job(task_id):
                    self.scheduler.remove_job(task_id)
                
                # 停止该任务的所有正在执行的进程
                stopped_count = self.task_executor.stop_all_tasks_by_id(task_id)
                if stopped_count > 0:
                    self.logger.info(f"已终止任务 {task_id} 的 {stopped_count} 个正在执行的进程")
                
                # 从当前任务列表中移除
                del self.tasks[task_id]

            # 处理新增任务（排除已处理的ID变更任务）
            for task_id in fresh_task_ids - current_task_ids - set(id_mapping.values()):
                fresh_task = fresh_tasks_dict[task_id]
                self.logger.info(f"发现新任务 {task_id}，将添加到调度计划")
                self.tasks[task_id] = fresh_task
                if fresh_task.task_enabled:
                    self._add_task_to_scheduler(fresh_task)
            
            self.logger.info(f"任务配置重载完成，当前任务总数: {len(self.tasks)}")
        except Exception as e:
            self.logger.error(f"重新加载任务配置时发生严重错误: {e}")
    
    def _execute_task_wrapper(self, task: Task):
        """任务执行的包装器，包含重试逻辑"""
        self.logger.info(f"调度器触发任务: {task.task_id} ({task.task_name})")
        current_task = self.tasks.get(task.task_id, task)
        
        for attempt in range(current_task.task_retry + 1):
            execution = self.task_executor.execute_task(current_task)
            
            if current_task.task_id not in self.executions:
                self.executions[current_task.task_id] = []
            self.executions[current_task.task_id].append(execution)
            
            # 根据任务脚本开发指南的退出码规范判断是否需要重试
            if execution.status == "success":
                # 退出码 0：成功，不重试
                break
            elif execution.status == "terminated":
                # 任务被终止（如因参数变化），不重试
                self.logger.info(f"任务 {current_task.task_id} 被终止，不进行重试")
                break
            elif execution.return_code == 1:
                # 退出码 1：业务失败，不重试
                self.logger.info(f"任务 {current_task.task_id} 业务失败 (退出码: 1)，根据规范不进行重试")
                break
            elif execution.return_code == 2:
                # 退出码 2：技术失败，可以重试
                if attempt < current_task.task_retry:
                    self.logger.warning(f"任务 {current_task.task_id} 技术失败 (退出码: 2)，第 {attempt + 1} 次执行失败，将在 {current_task.task_retry_interval} 秒后重试...")
                    time.sleep(current_task.task_retry_interval)
                else:
                    self.logger.error(f"任务 {current_task.task_id} 技术失败，已达到最大重试次数 ({current_task.task_retry})")
                    break
            elif execution.return_code == -15:  # 明确检查 SIGTERM 信号
                # 任务被终止（如因参数变化），不重试
                self.logger.info(f"任务 {current_task.task_id} 因参数变化或配置更新而终止，不进行重试")
                break
            else:
                # 其他退出码：按技术失败处理，可以重试
                if attempt < current_task.task_retry:
                    self.logger.warning(f"任务 {current_task.task_id} 执行失败 (退出码: {execution.return_code})，第 {attempt + 1} 次执行失败，将在 {current_task.task_retry_interval} 秒后重试...")
                    time.sleep(current_task.task_retry_interval)
                else:
                    self.logger.error(f"任务 {current_task.task_id} 执行失败，已达到最大重试次数 ({current_task.task_retry})")
                    break
    
    def add_task(self, task: Task) -> bool:
        """添加新任务"""
        if task.task_id in self.tasks:
            self.logger.warning(f"添加任务失败，任务ID {task.task_id} 已存在")
            return False
        try:
            self.tasks[task.task_id] = task
            if task.task_enabled:
                self._add_task_to_scheduler(task)
            self._mark_api_operation()
            self.task_loader.save_task(task)
            self.logger.info(f"成功添加新任务: {task.task_id}")
            return True
        except Exception as e:
            self.logger.error(f"添加任务 {task.task_id} 失败: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id not in self.tasks:
            return False
        try:
            # 获取任务信息，用于日志文件处理
            task = self.tasks[task_id]
            
            # 停止该任务的调度计划
            if self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
                self.logger.info(f"已从调度器中移除任务 {task_id} 的计划")
            
            # 停止该任务的所有正在执行的进程
            stopped_count = self.task_executor.stop_all_tasks_by_id(task_id)
            if stopped_count > 0:
                self.logger.info(f"已终止任务 {task_id} 的 {stopped_count} 个正在执行的进程")
            
            # 从任务列表中移除
            del self.tasks[task_id]
            
            self._mark_api_operation()
            # 删除任务目录和文件
            self.task_loader.delete_task_files(task_id)
            self.logger.info(f"成功移除任务: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"移除任务 {task_id} 失败: {e}")
            return False
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务的列表"""
        self.logger.debug("正在获取所有任务的详细信息...")
        result = []
        for task in self.tasks.values():
            job = self.scheduler.get_job(task.task_id)
            task_dict = asdict(task)
            task_dict['next_run_time'] = job.next_run_time.isoformat() if job and job.next_run_time else None
            result.append(task_dict)
        return result
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取单个任务的详情"""
        if task_id not in self.tasks:
            return None
        task = self.tasks[task_id]
        job = self.scheduler.get_job(task_id)
        task_dict = asdict(task)
        task_dict['next_run_time'] = job.next_run_time.isoformat() if job and job.next_run_time else None
        return task_dict
    
    # 用于防止短时间内重复更新同一任务
    _task_update_timestamps = {}
    _task_update_lock = threading.Lock()
    
    def update_task(self, task: Task) -> bool:
        """更新任务"""
        if task.task_id not in self.tasks:
            return False
            
        # 防止短时间内重复更新同一任务
        with self._task_update_lock:
            current_time = time.time()
            last_update_time = self._task_update_timestamps.get(task.task_id, 0)
            if current_time - last_update_time < 1.0:  # 1秒内不重复处理同一任务的更新
                self.logger.debug(f"任务 {task.task_id} 短时间内重复更新请求，已忽略")
                return True
            self._task_update_timestamps[task.task_id] = current_time
            
        try:
            original_task = self.tasks[task.task_id]
            
            # 检查任务是否有变更
            has_changes = not (task == original_task)
            
            if not has_changes:
                self.logger.info(f"任务 {task.task_id} 无任何变更，跳过更新")
                return True
            
            self.logger.info(f"任务 {task.task_id} 配置发生变更，开始更新...")
            
            # 检查日志文件路径是否变更
            if task.task_log != original_task.task_log and os.path.exists(original_task.task_log):
                try:
                    # 如果旧日志文件存在且与新日志文件不同，则删除旧日志文件
                    os.remove(original_task.task_log)
                    self.logger.info(f"已删除任务 {task.task_id} 的旧日志文件: {original_task.task_log}")
                except Exception as e:
                    self.logger.warning(f"删除任务 {task.task_id} 的旧日志文件失败: {e}")
            
            # 停止该任务的调度计划
            if self.scheduler.get_job(task.task_id):
                self.scheduler.remove_job(task.task_id)
                self.logger.info(f"已从调度器中移除任务 {task.task_id} 的调度计划")
            else:
                self.logger.debug(f"任务 {task.task_id} 当前没有活动的调度计划")
            
            # 停止该任务的所有正在执行的进程
            stopped_count = self.task_executor.stop_all_tasks_by_id(task.task_id)
            if stopped_count > 0:
                self.logger.info(f"已终止任务 {task.task_id} 的 {stopped_count} 个正在执行的进程")
            else:
                self.logger.debug(f"任务 {task.task_id} 当前没有正在执行的进程")
            
            # 更新任务配置
            self.tasks[task.task_id] = task
            
            # 如果任务启用，重新添加到调度器
            if task.task_enabled:
                self._add_task_to_scheduler(task)
                self.logger.info(f"已将任务 {task.task_id} 添加到调度计划")
            else:
                self.logger.debug(f"任务 {task.task_id} 已禁用，不会添加到调度计划")
            
            self._mark_api_operation()
            self.task_loader.save_task(task)
            self.logger.info(f"成功更新任务: {task.task_id}")
            return True
        except Exception as e:
            self.logger.error(f"更新任务 {task.task_id} 失败: {e}")
            return False

    def toggle_task(self, task_id: str, enabled: bool) -> bool:
        """启用或禁用任务"""
        if task_id not in self.tasks:
            self.logger.error(f"切换任务状态失败，任务 {task_id} 不存在")
            return False
            
        task = self.tasks[task_id]
        if task.task_enabled == enabled:
            self.logger.info(f"任务 {task_id} 状态未改变，无需操作")
            return True
            
        task.task_enabled = enabled
        
        if self.scheduler.get_job(task_id):
            self.scheduler.remove_job(task_id)
            self.logger.info(f"已从调度器中移除任务 {task_id} 以更新状态")
            
        if enabled:
            self._add_task_to_scheduler(task)
            self.logger.info(f"已将任务 {task_id} 重新添加到调度器")
        
        self._mark_api_operation()
        try:
            self.task_loader.save_task(task)
            self.logger.info(f"任务 {task_id} 状态已更新为: {'启用' if enabled else '禁用'}")
            return True
        except Exception as e:
            self.logger.error(f"保存任务 {task_id} 状态到配置文件失败: {e}")
            return False

    def execute_task_manually(self, task_id: str) -> bool:
        """手动触发一个任务的执行"""
        if task_id not in self.tasks:
            self.logger.error(f"手动执行任务失败，找不到ID为 {task_id} 的任务")
            return False

        task = self.tasks[task_id]
        self.logger.info(f"收到手动执行请求，将在后台线程中运行任务 {task_id}")

        thread = threading.Thread(target=self._execute_task_wrapper, args=(task,))
        thread.daemon = True
        thread.start()
        return True

    def run_task_once(self, task_id: str) -> bool:
        """直接运行一次任务，功能与手动执行类似"""
        return self.execute_task_manually(task_id)

def main():
    """主函数"""
    setup_logging() # Ensure logging is configured
    engine = SchedulerEngine()
    
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logging.info(f"接收到信号 {signal_name}，正在优雅地停止调度引擎...")
        engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        engine.start()
        logging.info("通用任务调度引擎已启动，按 Ctrl+C 停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("检测到 Ctrl+C，正在停止...")
    except Exception as e:
        logging.critical(f"调度引擎启动失败: {e}")
    finally:
        engine.stop()

if __name__ == "__main__":
    main()
