
import os
import signal
import subprocess
import time
import psutil
import logging
from typing import Dict, List, Optional, Any, Tuple

class ProcessManager:
    """进程管理器类，负责管理子进程的创建、监控和终止"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processes: Dict[str, subprocess.Popen] = {}
        
    def start_process(self, process_id: str, cmd: List[str], env: Dict[str, str] = None) -> Tuple[bool, Any]:
        """
        启动一个新进程
        """
        if process_id in self.processes:
            return False, f"进程 {process_id} 已在运行中"
            
        try:
            effective_env = os.environ.copy() if env is None else env
                
            process = subprocess.Popen(
                cmd,
                env=effective_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[process_id] = process
            self.logger.info(f"成功启动进程 {process_id}，PID: {process.pid}")
            
            return True, process
            
        except Exception as e:
            self.logger.error(f"启动进程 {process_id} 失败: {e}")
            return False, str(e)
    
    def stop_process(self, process_id: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        停止指定的进程
        """
        if process_id not in self.processes:
            return False, f"进程 {process_id} 不存在或已停止"
            
        process = self.processes[process_id]
        
        try:
            if process.poll() is not None:
                del self.processes[process_id]
                return True, f"进程 {process_id} 在停止前已经终止"
                
            self.logger.info(f"正在尝试正常停止进程 {process_id} (PID: {process.pid})...")
            process.terminate()
            
            try:
                process.wait(timeout=timeout)
                del self.processes[process_id]
                self.logger.info(f"进程 {process_id} 已被正常终止")
                return True, f"进程 {process_id} 已被正常终止"
            except subprocess.TimeoutExpired:
                self.logger.warning(f"正常停止进程 {process_id} 超时，将强制终止...")
                process.kill()
                process.wait(timeout=1)
                del self.processes[process_id]
                self.logger.warning(f"进程 {process_id} 已被强制终止")
                return True, f"进程 {process_id} 被强制终止"
                
        except Exception as e:
            self.logger.error(f"停止进程 {process_id} 时发生异常: {e}")
            return False, str(e)
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """
        获取进程状态
        """
        if process_id not in self.processes:
            return {"exists": False}
            
        process = self.processes[process_id]
        
        try:
            if process.poll() is not None:
                del self.processes[process_id]
                return {"exists": False, "running": False, "exit_code": process.returncode}
                
            try:
                proc = psutil.Process(process.pid)
                return {
                    "exists": True,
                    "running": True,
                    "pid": process.pid,
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_rss": proc.memory_info().rss,
                    "memory_vms": proc.memory_info().vms,
                    "create_time": proc.create_time()
                }
            except psutil.NoSuchProcess:
                del self.processes[process_id]
                return {"exists": False, "running": False}
                
        except Exception as e:
            self.logger.error(f"获取进程 {process_id} 状态时发生异常: {e}")
            return {"exists": True, "running": "unknown", "error": str(e)}
    
    def get_process_output(self, process_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        获取进程的输出
        """
        if process_id not in self.processes:
            return False, {"error": f"进程 {process_id} 不存在"}
            
        process = self.processes[process_id]
        
        try:
            is_running = process.poll() is None
            
            stdout_data = process.stdout.read1(4096) if process.stdout and hasattr(process.stdout, 'read1') else b""
            stderr_data = process.stderr.read1(4096) if process.stderr and hasattr(process.stderr, 'read1') else b""
                
            return True, {
                "running": is_running,
                "stdout": stdout_data.decode('utf-8', errors='replace'),
                "stderr": stderr_data.decode('utf-8', errors='replace'),
                "exit_code": process.returncode if not is_running else None
            }
            
        except Exception as e:
            self.logger.error(f"获取进程 {process_id} 输出时发生异常: {e}")
            return False, {"error": str(e)}
    
    def cleanup(self):
        """清理所有正在运行的进程"""
        self.logger.info("开始清理所有由进程管理器启动的进程...")
        for process_id in list(self.processes.keys()):
            self.stop_process(process_id)
        self.logger.info("所有进程已清理完毕")


# 全局进程管理器实例
_process_manager = None

def get_process_manager():
    """获取进程管理器单例"""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager
