

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
    """配置文件变更监控处理器"""
    
    def __init__(self, scheduler_engine, config_file: str):
        super().__init__()
        self.scheduler_engine = scheduler_engine
        self.config_file = os.path.abspath(config_file)
        self.logger = logging.getLogger(__name__)
        self.last_modified = 0
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory or os.path.abspath(event.src_path) != self.config_file:
            return
            
        current_time = time.time()
        if current_time - self.last_modified < 1:
            return
        self.last_modified = current_time
        
        self.logger.info(f"检测到配置文件变更: {event.src_path}，准备重新加载任务...")
        time.sleep(0.5)
        self.scheduler_engine._reload_all_tasks()

class TaskLoader:
    """任务加载器"""
    
    def __init__(self, config_file: str = "tasks/config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        
    def load_tasks(self) -> List[Task]:
        """从配置文件加载所有任务"""
        if not os.path.exists(self.config_file):
            self.logger.info(f"配置文件 {self.config_file} 不存在，将创建默认配置。")
            self._create_default_config()
            return []
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            task_list = data if isinstance(data, list) else data.get('tasks', [])
            if not task_list:
                self.logger.warning("配置文件格式错误或任务列表为空。")
                return []
                
            tasks = []
            for task_data in task_list:
                try:
                    task = Task(**task_data)
                    if self._validate_task(task):
                        tasks.append(task)
                    else:
                        self.logger.warning(f"任务 {task.task_id} 配置无效，已跳过。")
                except TypeError as e:
                    self.logger.error(f"加载任务数据失败，字段不匹配: {task_data}，错误: {e}")
                except Exception as e:
                    self.logger.error(f"解析任务配置时发生未知错误: {e}")
                    
            return tasks
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析配置文件 {self.config_file} 失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"加载任务配置文件时发生未知错误: {e}")
            return []
    
    def save_tasks(self, tasks: List[Task]):
        """保存任务到配置文件"""
        try:
            data = {"tasks": [asdict(task) for task in tasks]}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"成功保存 {len(tasks)} 个任务到配置文件 {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存任务配置到文件失败: {e}")
    
    def _validate_task(self, task: Task) -> bool:
        """验证任务配置"""
        if not all([task.task_id, task.task_name, task.task_exec]):
            self.logger.warning(f"任务验证失败，缺少必要字段 (ID, 名称, 执行命令): {task.task_id}")
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
                    "task_env": {"PARAM1": "值1"},
                    "task_dependencies": [],
                    "task_notify": {"on_success": False, "on_failure": True}
                }
            ]
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_tasks, f, indent=2, ensure_ascii=False)
            self.logger.info(f"已成功创建默认配置文件: {self.config_file}")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")

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
        
        try:
            env = self._prepare_environment(task)
            os.makedirs(os.path.dirname(task.task_log), exist_ok=True)
            self._clear_python_module_cache(task.task_exec)
            
            cmd, shell = self._prepare_command(task.task_exec)
            
            with open(task.task_log, 'w', encoding='utf-8') as log_file:
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
            self.logger.info(f"任务 {task.task_id} 指定了环境文件: {env_file_path}")
            if os.path.exists(env_file_path):
                try:
                    env.update(dotenv_values(env_file_path))
                    self.logger.info(f"成功从 {env_file_path} 加载环境变量")
                except Exception as e:
                    self.logger.error(f"加载环境文件 {env_file_path} 失败: {e}")
            else:
                self.logger.warning(f"环境文件 {env_file_path} 不存在，已跳过")

        env.update(task_env_config)
        env['TASK_ID'] = task.task_id
        env['TASK_LOG'] = task.task_log
        
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
            SchedulerEngine._initialized = True
        
    def start(self):
        """启动调度引擎"""
        self.logger.info("正在启动任务调度引擎...")
        tasks = self.task_loader.load_tasks()
        self.logger.info(f"成功加载 {len(tasks)} 个任务")
        
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
        """启动配置文件监控"""
        try:
            config_path = self.task_loader.config_file
            if not os.path.exists(config_path):
                self.logger.warning(f"配置文件 {config_path} 不存在，跳过文件监控")
                return
                
            self.config_handler = ConfigFileHandler(self, config_path)
            self.file_observer = Observer()
            config_dir = os.path.dirname(os.path.abspath(config_path))
            self.file_observer.schedule(self.config_handler, config_dir, recursive=False)
            self.file_observer.start()
            self.logger.info(f"已启动对配置文件 {config_path} 的监控")
        except Exception as e:
            self.logger.error(f"启动配置文件监控失败: {e}")
    
    def _stop_file_monitoring(self):
        """停止文件监控"""
        try:
            if self.file_observer and self.file_observer.is_alive():
                self.file_observer.stop()
                self.file_observer.join(timeout=5)
                self.logger.info("已停止配置文件监控")
        except Exception as e:
            self.logger.error(f"停止文件监控时发生异常: {e}")
    
    def _mark_api_operation(self):
        """标记API操作，用于短期内忽略文件变更事件"""
        with self.api_operation_lock:
            self.api_operation_timestamp = time.time()
            self.logger.debug("已标记API操作时间戳，以避免不必要的重载")
    
    def _is_api_operation_recent(self) -> bool:
        """检查文件变更是否由最近的API操作触发"""
        with self.api_operation_lock:
            return (time.time() - self.api_operation_timestamp) < 2
    
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

            # 更新和检测变更
            for task_id in current_task_ids.intersection(fresh_task_ids):
                fresh_task = fresh_tasks_dict[task_id]
                if fresh_task.has_critical_changes(self.tasks[task_id]):
                    self.logger.info(f"任务 {task_id} 的关键配置发生变更，将重新调度")
                    if self.scheduler.get_job(task_id):
                        self.scheduler.remove_job(task_id)
                    if fresh_task.task_enabled:
                        self._add_task_to_scheduler(fresh_task)
                self.tasks[task_id] = fresh_task

            # 删除任务
            for task_id in current_task_ids - fresh_task_ids:
                self.logger.info(f"任务 {task_id} 已从配置文件中移除，将停止调度")
                if self.scheduler.get_job(task_id):
                    self.scheduler.remove_job(task_id)
                del self.tasks[task_id]

            # 新增任务
            for task_id in fresh_task_ids - current_task_ids:
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
            self.task_loader.save_tasks(list(self.tasks.values()))
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
            if self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
            del self.tasks[task_id]
            self._mark_api_operation()
            self.task_loader.save_tasks(list(self.tasks.values()))
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
    
    def update_task(self, task: Task) -> bool:
        """更新任务"""
        if task.task_id not in self.tasks:
            return False
        try:
            original_task = self.tasks[task.task_id]
            if task == original_task:
                self.logger.info(f"任务 {task.task_id} 无任何变更，跳过更新")
                return True
                
            if self.scheduler.get_job(task.task_id):
                self.scheduler.remove_job(task.task_id)
                
            self.tasks[task.task_id] = task
            if task.task_enabled:
                self._add_task_to_scheduler(task)
            
            self._mark_api_operation()
            self.task_loader.save_tasks(list(self.tasks.values()))
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
            self.task_loader.save_tasks(list(self.tasks.values()))
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
