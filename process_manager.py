import os
import signal
import subprocess
import time
import psutil
from typing import Dict, List, Optional, Any, Tuple
from logger_helper import LoggerHelper

class ProcessManager:
    """进程管理器类，负责管理子进程的创建、监控和终止"""
    
    def __init__(self):
        self.logger = LoggerHelper.get_system_logger(__name__)
        self.processes: Dict[str, subprocess.Popen] = {}
        
    def start_process(self, process_id: str, cmd: List[str], env: Dict[str, str] = None) -> Tuple[bool, Any]:
        """
        启动一个新进程
        
        Args:
            process_id: 进程ID
            cmd: 命令行参数列表
            env: 环境变量字典
            
        Returns:
            (成功标志, 进程对象或错误消息)
        """
        if process_id in self.processes:
            return False, f"进程 {process_id} 已存在"
            
        try:
            # 如果没有提供环境变量，使用当前环境
            if env is None:
                env = os.environ.copy()
                
            # 创建进程
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[process_id] = process
            self.logger.info(f"进程 {process_id} 已启动，PID: {process.pid}")
            
            return True, process
            
        except Exception as e:
            self.logger.error(f"启动进程 {process_id} 失败: {str(e)}")
            return False, str(e)
    
    def stop_process(self, process_id: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        停止指定的进程
        
        Args:
            process_id: 进程ID
            timeout: 等待进程终止的超时时间（秒）
            
        Returns:
            (成功标志, 消息)
        """
        if process_id not in self.processes:
            return False, f"进程 {process_id} 不存在"
            
        process = self.processes[process_id]
        
        try:
            # 检查进程是否已经终止
            if process.poll() is not None:
                del self.processes[process_id]
                return True, f"进程 {process_id} 已经终止"
                
            # 发送SIGTERM信号
            process.terminate()
            
            # 等待进程终止
            try:
                process.wait(timeout=timeout)
                del self.processes[process_id]
                return True, f"进程 {process_id} 已正常终止"
            except subprocess.TimeoutExpired:
                # 如果超时，发送SIGKILL信号
                process.kill()
                process.wait(timeout=1)
                del self.processes[process_id]
                return True, f"进程 {process_id} 被强制终止"
                
        except Exception as e:
            self.logger.error(f"停止进程 {process_id} 失败: {str(e)}")
            return False, str(e)
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """
        获取进程状态
        
        Args:
            process_id: 进程ID
            
        Returns:
            进程状态信息
        """
        if process_id not in self.processes:
            return {"exists": False}
            
        process = self.processes[process_id]
        
        try:
            # 检查进程是否仍在运行
            is_running = process.poll() is None
            
            # 如果进程已终止，从字典中删除
            if not is_running:
                del self.processes[process_id]
                return {
                    "exists": False,
                    "running": False,
                    "exit_code": process.returncode
                }
                
            # 获取进程详细信息
            try:
                proc = psutil.Process(process.pid)
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_info = proc.memory_info()
                
                return {
                    "exists": True,
                    "running": True,
                    "pid": process.pid,
                    "cpu_percent": cpu_percent,
                    "memory_rss": memory_info.rss,
                    "memory_vms": memory_info.vms,
                    "create_time": proc.create_time()
                }
            except psutil.NoSuchProcess:
                # 进程可能刚刚终止
                del self.processes[process_id]
                return {
                    "exists": False,
                    "running": False
                }
                
        except Exception as e:
            self.logger.error(f"获取进程 {process_id} 状态失败: {str(e)}")
            return {
                "exists": True,
                "running": "unknown",
                "error": str(e)
            }
    
    def get_process_output(self, process_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        获取进程的输出
        
        Args:
            process_id: 进程ID
            
        Returns:
            (成功标志, 输出信息)
        """
        if process_id not in self.processes:
            return False, {"error": f"进程 {process_id} 不存在"}
            
        process = self.processes[process_id]
        
        try:
            # 检查进程是否仍在运行
            is_running = process.poll() is None
            
            # 获取当前可用的输出
            stdout_data = b""
            stderr_data = b""
            
            if process.stdout:
                stdout_data = process.stdout.read1(4096) if hasattr(process.stdout, 'read1') else b""
                
            if process.stderr:
                stderr_data = process.stderr.read1(4096) if hasattr(process.stderr, 'read1') else b""
                
            return True, {
                "running": is_running,
                "stdout": stdout_data.decode('utf-8', errors='replace') if stdout_data else "",
                "stderr": stderr_data.decode('utf-8', errors='replace') if stderr_data else "",
                "exit_code": process.returncode if not is_running else None
            }
            
        except Exception as e:
            self.logger.error(f"获取进程 {process_id} 输出失败: {str(e)}")
            return False, {"error": str(e)}
    
    def cleanup(self):
        """清理所有进程"""
        for process_id in list(self.processes.keys()):
            self.stop_process(process_id)
            
        self.logger.info("进程管理器已清理所有进程")


# 全局进程管理器实例
_process_manager = None

def get_process_manager():
    """获取进程管理器单例"""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager