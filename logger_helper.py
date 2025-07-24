
import os
import logging
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Any, Optional

def setup_logging():
    """
    配置全局日志系统。
    此函数应在应用程序启动时只调用一次。
    它会配置根日志记录器，所有通过 logging.getLogger(__name__) 创建的子记录器都会继承此配置。
    """
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return

    log_level_str = os.getenv('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # 设置第三方库的日志级别
    logging.getLogger('apscheduler').setLevel(logging.WARNING)  # 减少APScheduler的日志输出
    logging.getLogger('apscheduler.scheduler').setLevel(logging.WARNING)
    logging.getLogger('watchdog.observers.inotify_buffer').setLevel(logging.WARNING)

    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)

    # 创建一个通用的格式化器
    formatter = logging.Formatter(
        '[%(asctime)s] <%(levelname)s> %(name)s: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器根据环境变量设置日志级别
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器记录所有级别
    sys_log_file = os.path.join(logs_dir, "sys.log")
    file_handler = RotatingFileHandler(
        sys_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger(__name__).info("全局日志系统配置完成。")

def get_task_logger(task_id: str):
    """
    获取任务专用的日志记录器。
    - 只将日志记录到独立的任务日志文件。
    - 不将日志传播到根记录器，避免在控制台或系统日志中重复显示。
    """
    log_level_str = os.getenv('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    logger_name = f"task_{task_id}"
    task_logger = logging.getLogger(logger_name)
    task_logger.setLevel(log_level)
    task_logger.propagate = False  # 核心：阻止日志向上传播

    # 如果已经配置过处理器，则直接返回，避免重复添加
    if task_logger.hasHandlers():
        return task_logger

    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"task_{task_id}.log")

    # 使用与系统日志相同的格式,保持一致性
    formatter = logging.Formatter(
        '[%(asctime)s] <%(levelname)s> %(name)s: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    task_logger.addHandler(file_handler)

    return task_logger

class LoggerHelper:
    """日志帮助类，提供日志读取功能"""

    @staticmethod
    def read_logs(log_file: Optional[str] = None, task_id: Optional[str] = None,
                  level: Optional[str] = None, limit: int = 100,
                  offset: int = 0) -> Dict[str, Any]:
        """
        读取和过滤日志
        """
        try:
            if not log_file:
                log_file = f"logs/task_{task_id}.log" if task_id else "logs/sys.log"
            
            if not os.path.exists(log_file):
                return {
                    "success": True,
                    "logs": [{"raw": "暂无日志信息，请等待任务执行..."}],
                    "total": 0,
                    "has_more": False
                }
                
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            log_entries = [entry for line in lines if (entry := LoggerHelper._parse_log_line(line)) 
                           and (not level or entry.get('level') == level)]
            
            total_entries = len(log_entries)
            paginated_entries = log_entries[offset:offset+limit]
            
            return {
                "success": True,
                "logs": paginated_entries,
                "total": total_entries,
                "has_more": offset + limit < total_entries
            }
            
        except Exception as e:
            return {"success": False, "message": f"读取日志失败: {str(e)}"}
    
    @staticmethod
    def _parse_log_line(line: str) -> Optional[Dict[str, Any]]:
        """
        解析单行日志
        """
        # 匹配新格式: 2023-10-27 10:30:00 - module.name - INFO - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([a-zA-Z0-9._]+) - (INFO|WARNING|ERROR|DEBUG|CRITICAL) - (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp_str, name, level, message = match.groups()
            return {
                "timestamp": timestamp_str,
                "name": name.strip(),
                "level": level.strip(),
                "message": message.strip()
            }
        
        # 匹配旧的任务日志格式，以提供向后兼容性
        task_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (INFO|WARNING|ERROR|DEBUG|CRITICAL) - (.+)'
        task_match = re.match(task_pattern, line)
        if task_match:
            timestamp_str, level, message = task_match.groups()
            return {
                "timestamp": timestamp_str,
                "name": "task",
                "level": level.strip(),
                "message": message.strip()
            }

        # 如果不匹配任何已知格式，则作为原始行返回
        if line.strip():
            return {"timestamp": "", "name": "raw", "level": "INFO", "message": line.strip()}
        
        return None
