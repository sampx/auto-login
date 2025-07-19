import os
import time
import signal
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from logger_helper import LoggerHelper

class Task:
    """任务模型类，表示一个自动登录任务"""
    
    def __init__(self, task_id: str, name: str, description: str, config: Dict[str, Any], command: str = None):
        self.id = task_id
        self.name = name
        self.description = description
        self.status = "stopped"  # 初始状态为停止
        self.config = config
        self.command = command or "python auto_login.py"  # 默认执行命令
        self.process = None
        self.pid = None
        self.last_run = None
        self.next_run = None
        self.schedule = self._format_schedule()
        self.enabled = True  # 任务是否启用
        
    def _format_schedule(self) -> str:
        """格式化调度信息为人类可读的字符串"""
        schedule_type = self.config.get("LOGIN_SCHEDULE_TYPE")
        
        if schedule_type == "monthly":
            date = self.config.get("LOGIN_SCHEDULE_DATE", "1")
            time = self.config.get("LOGIN_SCHEDULE_TIME", "00:00")
            return f"每月{date}日 {time}"
        elif schedule_type == "minutes":
            return f"每3分钟"
        else:
            return "未知调度"


class TaskManager:
    """任务管理器类，负责管理自动登录任务"""
    
    def __init__(self):
        self.logger = LoggerHelper.get_system_logger(__name__)
        self.tasks: Dict[str, Task] = {}
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.load_tasks()
        
    def load_tasks(self):
        """从环境变量加载任务配置"""
        load_dotenv()
        
        # 创建默认的自动登录任务
        default_task = Task(
            task_id="auto_login",
            name="自动登录任务",
            description="定期执行网站自动登录，保持账号活跃",
            config={
                "WEBSITE_URL": os.getenv("WEBSITE_URL"),
                "USERNAME": os.getenv("USERNAME"),
                "PASSWORD": os.getenv("PASSWORD"),
                "MAX_RETRIES": os.getenv("MAX_RETRIES"),
                "LOGIN_SCHEDULE_TYPE": os.getenv("LOGIN_SCHEDULE_TYPE"),
                "LOGIN_SCHEDULE_DATE": os.getenv("LOGIN_SCHEDULE_DATE"),
                "LOGIN_SCHEDULE_TIME": os.getenv("LOGIN_SCHEDULE_TIME")
            },
            command="python auto_login.py"
        )
        
        self.tasks[default_task.id] = default_task
        self.logger.info(f"已加载任务: {default_task.name}")
        
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务的列表"""
        result = []
        for task_id, task in self.tasks.items():
            result.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "command": task.command,
                "status": task.status,
                "enabled": task.enabled,
                "schedule": task.schedule,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None
            })
        return result
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取指定任务的详细信息"""
        task = self.tasks.get(task_id)
        if not task:
            return None
            
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "command": task.command,
            "status": task.status,
            "enabled": task.enabled,
            "schedule": task.schedule,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "config": task.config
        }
    
    def start_task(self, task_id: str) -> Dict[str, Any]:
        """启动指定的任务"""
        # 使用锁确保任务启动的线程安全
        with threading.Lock():
            task = self.tasks.get(task_id)
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}
                
            if not task.enabled:
                return {"success": False, "message": f"任务 {task_id} 已被禁用，无法启动"}
                
            if task.status == "running":
                return {"success": False, "message": f"任务 {task_id} 已经在运行中"}
                
            # 检查是否已经有相同类型的进程在运行
            try:
                import subprocess
                ps_output = subprocess.check_output(["ps", "-ef"], text=True)
                count = 0
                
                # 查找包含auto_login.py的进程
                for line in ps_output.splitlines():
                    if "auto_login.py" in line and "python" in line:
                        count += 1
                
                # 如果已经有进程在运行，则不启动新进程
                if count > 0:
                    self.logger.warning(f"检测到已有 {count} 个auto_login.py进程在运行，不再启动新进程")
                    return {"success": False, "message": f"已有相同类型的进程在运行，请先停止现有进程"}
            except Exception as e:
                self.logger.warning(f"检查进程状态失败: {str(e)}")
            
            # 如果之前有进程残留，先清理
            if task.process is not None:
                try:
                    if task.process.poll() is None:
                        task.process.terminate()
                        task.process.wait(timeout=3)
                except:
                    pass
                finally:
                    task.process = None
                    task.pid = None
                
            try:
                # 启动任务进程
                cmd = ["python", "auto_login.py"]
                
                # 创建环境变量副本
                env = os.environ.copy()
                
                # 将任务配置添加到环境变量
                for key, value in task.config.items():
                    if value is not None:
                        env[key] = str(value)
                
                # 启动进程
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True
                )
                
                task.process = process
                task.pid = process.pid
                task.pgid = os.getpgid(process.pid)
                task.status = "running"
                task.last_run = datetime.now()
                
                # 启动监控线程
                monitor_thread = threading.Thread(
                    target=self._monitor_task_process,
                    args=(task_id,),
                    daemon=True
                )
                monitor_thread.start()
                
                # 记录到系统日志
                self.logger.info(f"任务 {task_id} 状态变更为: running，PID: {task.pid}")
                
                return {"success": True, "message": f"任务 {task_id} 已启动"}
                
            except Exception as e:
                self.logger.error(f"启动任务 {task_id} 失败: {str(e)}")
                return {"success": False, "message": f"启动任务失败: {str(e)}"}
    
    def stop_task(self, task_id: str) -> Dict[str, Any]:
        """停止指定的任务及其所有子进程"""
        with threading.Lock():
            task = self.tasks.get(task_id)
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}

            if task.status != "running" or not task.process or not task.pid:
                return {"success": False, "message": f"任务 {task_id} 未在运行"}

            if not hasattr(task, 'pgid') or not task.pgid:
                self.logger.error(f"任务 {task_id} 缺少PGID, 无法停止。可能启动时出错。")
                return {"success": False, "message": f"任务 {task_id} 缺少进程组ID，无法停止"}

            pid = task.pid
            pgid = task.pgid
            self.logger.info(f"正在尝试停止任务 {task_id} (PID: {pid}, PGID: {pgid})...")

            try:
                # 检查进程组是否存在
                os.killpg(pgid, 0)

                # 1. 发送SIGTERM信号，尝试优雅地终止整个进程组
                self.logger.info(f"向任务 {task_id} (PGID: {pgid}) 发送SIGTERM信号...")
                os.killpg(pgid, signal.SIGTERM)

                # 2. 等待最多10秒，让主进程自己退出
                try:
                    task.process.wait(timeout=10)
                    self.logger.info(f"任务 {task_id} (PID: {pid}) 在接收到SIGTERM后成功终止。")
                except subprocess.TimeoutExpired:
                    # 3. 如果10秒后仍在运行，发送SIGKILL强制终止整个进程组
                    self.logger.warning(f"任务 {task_id} (PID: {pid}) 未在10秒内响应SIGTERM，发送SIGKILL强制终止...")
                    os.killpg(pgid, signal.SIGKILL)
                    task.process.wait(timeout=2)
                    self.logger.info(f"任务 {task_id} (PGID: {pgid}) 已被SIGKILL强制终止。")
                
                return {"success": True, "message": f"已向任务 {task_id} 发送停止信号，等待其完全终止。"}

            except ProcessLookupError:
                self.logger.warning(f"尝试停止任务 {task_id} 时，进程组 (PGID: {pid}) 已不存在。")
                # 进程已消失，监控线程会处理状态更新
                return {"success": True, "message": f"任务 {task_id} 进程已不存在"}
            except Exception as e:
                self.logger.error(f"停止任务 {task_id} (PID: {pid}) 时发生未知错误: {str(e)}")
                task.status = "stopped"
                task.process = None
                task.pid = None
                return {"success": False, "message": f"停止任务时发生错误: {str(e)}"}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取指定任务的状态"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "message": f"任务 {task_id} 不存在"}
            
        # 检查进程状态
        if task.process and task.process.poll() is None:
            task.status = "running"
        else:
            # 如果进程不存在或已终止，确保状态为stopped
            if task.status == "running":
                # 进程已经终止但状态未更新
                task.status = "stopped"
                task.process = None
                task.pid = None
                self.logger.info(f"任务 {task_id} 状态自动更新为: stopped (进程已终止)")
            
        return {
            "success": True,
            "status": task.status,
            "enabled": task.enabled,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None
        }
    
    def get_task_logs(self, task_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """获取指定任务的日志"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "message": f"任务 {task_id} 不存在"}
            
        try:
            # 使用LoggerHelper来获取日志
            from logger_helper import LoggerHelper
            result = LoggerHelper.read_logs(
                task_id=task_id,
                limit=limit,
                offset=offset
            )
            
            if result["success"]:
                # 如果没有日志，返回提示信息
                if not result["logs"]:
                    return {
                        "success": True,
                        "logs": [{"raw": "暂无日志信息，请等待任务执行..."}],
                        "total": 0,
                        "has_more": False
                    }
                return result
            else:
                return result
                    
        except Exception as e:
            # 记录到系统日志
            self.logger.error(f"获取任务 {task_id} 日志失败: {str(e)}")
            return {"success": False, "message": f"获取日志失败: {str(e)}"}
    
    def _monitor_task_process(self, task_id: str):
        """监控任务进程的状态"""
        task = self.tasks.get(task_id)
        if not task or not task.process:
            return
            
        try:
            # 等待进程结束
            task.process.wait()
            
            # 更新任务状态
            task.status = "stopped"
            task.process = None
            task.pid = None
            
            # 写入任务日志，表示任务已结束
            from logger_helper import LoggerHelper
            task_logger = LoggerHelper.get_task_logger(task_id)
            task_logger.info(f"任务已结束")
            
            # 写入系统日志，记录任务状态变化
            self.logger.info(f"任务 {task_id} 状态变更为: stopped")
        except Exception as e:
            self.logger.error(f"监控任务 {task_id} 进程时发生错误: {str(e)}")
            # 即使出错也要重置状态
            task.status = "stopped"
            task.process = None
            task.pid = None
        
    def toggle_task_enabled(self, task_id: str, enabled: bool) -> Dict[str, Any]:
        """启用或禁用任务"""
        with threading.Lock():
            task = self.tasks.get(task_id)
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}
                
            if task.enabled == enabled:
                status_text = "启用" if enabled else "禁用"
                return {"success": False, "message": f"任务已经是{status_text}状态"}
                
            # 如果任务正在运行，先停止它
            if task.status == "running" and not enabled:
                self.stop_task(task_id)
                
            task.enabled = enabled
            status_text = "启用" if enabled else "禁用"
            self.logger.info(f"任务 {task_id} 已{status_text}")
            
            return {
                "success": True, 
                "message": f"任务 {task_id} 已{status_text}",
                "enabled": task.enabled
            }

    def cleanup(self):
        """清理资源，停止所有任务"""
        for task_id in list(self.tasks.keys()):
            try:
                # 尝试停止任务，但忽略错误
                self.stop_task(task_id)
            except Exception as e:
                self.logger.error(f"清理任务 {task_id} 时发生错误: {str(e)}")
            
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.shutdown()
            except Exception as e:
                self.logger.error(f"关闭调度器时发生错误: {str(e)}")
            
        self.logger.info("任务管理器已清理所有资源")


# 全局任务管理器实例
_task_manager = None
_task_manager_lock = threading.Lock()

def get_task_manager() -> TaskManager:
    """获取任务管理器单例（线程安全）"""
    global _task_manager
    if _task_manager is None:
        with _task_manager_lock:
            if _task_manager is None:  # 双重检查
                _task_manager = TaskManager()
    return _task_manager