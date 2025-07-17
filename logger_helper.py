import os
import logging
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Any, Optional

class LoggerHelper:
    """日志帮助类，提供日志配置和读取功能"""
    
    @staticmethod
    def get_system_logger(name):
        """
        获取系统日志记录器 - 同时输出到控制台和系统日志文件
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的系统日志记录器
        """
        # 获取环境变量中的日志级别，默认为INFO
        log_level_str = os.getenv('LOG_LEVEL', 'INFO')
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        # 创建日志目录（如果不存在）
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)
        
        # 系统日志文件
        log_file = f"{logs_dir}/sys.log"
        logger_name = f"system_{name}"
        
        # 创建日志记录器
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        
        # 清除现有的处理器
        if logger.handlers:
            logger.handlers.clear()
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 创建文件处理器（使用RotatingFileHandler进行日志轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 设置格式化器
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def get_task_logger(task_id):
        """
        获取任务日志记录器 - 只记录到任务日志文件，不输出到控制台或系统日志
        
        Args:
            task_id: 任务ID
            
        Returns:
            配置好的任务日志记录器
        """
        # 获取环境变量中的日志级别，默认为INFO
        log_level_str = os.getenv('LOG_LEVEL', 'INFO')
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        # 创建日志目录（如果不存在）
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)
        
        # 任务特定日志文件
        log_file = f"{logs_dir}/task_{task_id}.log"
        logger_name = f"task_{task_id}"
        
        # 创建日志记录器
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = False  # 防止日志传播到根记录器
        
        # 清除现有的处理器
        if logger.handlers:
            logger.handlers.clear()
        
        # 创建文件处理器（使用RotatingFileHandler进行日志轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # 创建格式化器 - 任务日志格式更简洁
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 设置格式化器
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        
        return logger

    @staticmethod
    def read_logs(log_file: str = None, task_id: Optional[str] = None, 
                  level: Optional[str] = None, limit: int = 100, 
                  offset: int = 0) -> Dict[str, Any]:
        """
        读取和过滤日志
        
        Args:
            log_file: 日志文件路径，默认为环境变量中的LOG_FILE
            task_id: 任务ID过滤器
            level: 日志级别过滤器
            limit: 返回的日志条数限制
            offset: 日志条数偏移量
            
        Returns:
            过滤后的日志条目
        """
        try:
            # 获取日志文件路径
            if not log_file:
                if task_id:
                    # 使用任务特定的日志文件
                    log_file = f"logs/task_{task_id}.log"
                else:
                    # 使用系统日志文件
                    log_file = "logs/sys.log"
                
            # 检查日志文件是否存在
            if not os.path.exists(log_file):
                return {
                    "success": True,
                    "logs": [{"raw": "暂无日志信息，请等待任务执行..."}],
                    "total": 0,
                    "has_more": False
                }
                
            # 读取日志文件
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 解析日志行
            log_entries = []
            for line in lines:
                # 解析日志行
                entry = LoggerHelper._parse_log_line(line)
                if entry:
                    # 应用过滤器
                    if level and entry.get('level') != level:
                        continue
                        
                    log_entries.append(entry)
            
            # 应用分页
            total_entries = len(log_entries)
            paginated_entries = log_entries[offset:offset+limit]
            
            return {
                "success": True,
                "logs": paginated_entries,
                "total": total_entries,
                "has_more": offset + limit < total_entries
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"读取日志失败: {str(e)}"
            }
    
    @staticmethod
    def _parse_log_line(line: str) -> Optional[Dict[str, Any]]:
        """
        解析日志行
        
        Args:
            line: 日志行文本
            
        Returns:
            解析后的日志条目，如果解析失败则返回None
        """
        try:
            # 尝试匹配标准格式：时间戳 - 名称 - 级别 - 消息
            pattern1 = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - ([^-]+) - (.+)'
            match1 = re.match(pattern1, line)
            
            if match1:
                timestamp_str, name, level, message = match1.groups()
                
                # 解析时间戳
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except ValueError:
                    timestamp = None
                    
                return {
                    "timestamp": timestamp.isoformat() if timestamp else timestamp_str,
                    "name": name.strip(),
                    "level": level.strip(),
                    "message": message.strip()
                }
            
            # 尝试匹配任务日志格式：时间戳 - 级别 - 消息
            pattern2 = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (.+)'
            match2 = re.match(pattern2, line)
            
            if match2:
                timestamp_str, level, message = match2.groups()
                
                # 解析时间戳
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except ValueError:
                    timestamp = None
                
                return {
                    "timestamp": timestamp.isoformat() if timestamp else timestamp_str,
                    "name": "task",
                    "level": level.strip(),
                    "message": message.strip()
                }
            
            # 如果不匹配任何格式，返回原始行
            return {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "name": "system",
                "message": line.strip()
            }
                
        except Exception:
            # 解析失败，返回原始行
            return {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "name": "system",
                "message": line.strip()
            }

# 添加日志查看API路由
def add_log_routes(app):
    """
    添加日志查看API路由
    
    Args:
        app: Flask应用实例
    """
    from flask import request, jsonify
    
    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        """获取系统日志"""
        try:
            # 获取查询参数
            level = request.args.get('level')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            # 读取系统日志
            result = LoggerHelper.read_logs(
                log_file="logs/sys.log",
                level=level,
                limit=limit,
                offset=offset
            )
            
            if result["success"]:
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"获取日志失败: {str(e)}"
            }), 500
            
    @app.route('/api/tasks/<task_id>/logs', methods=['GET'])
    def get_task_logs(task_id):
        """获取指定任务的日志"""
        try:
            # 获取查询参数
            level = request.args.get('level')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            # 读取任务日志
            result = LoggerHelper.read_logs(
                task_id=task_id,
                level=level,
                limit=limit,
                offset=offset
            )
            
            if result["success"]:
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"获取任务日志失败: {str(e)}"
            }), 500
            
    @app.route('/api/tasks/<task_id>/logs/clear', methods=['POST'])
    def clear_task_logs(task_id):
        """清空指定任务的日志文件内容"""
        try:
            log_file = f"logs/task_{task_id}.log"
            
            if os.path.exists(log_file):
                # 清空文件内容而不是删除文件
                with open(log_file, 'w') as f:
                    f.write("")
                
                # 写入一条初始日志，表示日志已清空
                task_logger = LoggerHelper.get_task_logger(task_id)
                task_logger.info("日志已清空，等待新日志...")
                
                # 记录到系统日志
                sys_logger = LoggerHelper.get_system_logger("logger_helper")
                sys_logger.info(f"任务 {task_id} 的日志已清空")
                
                return jsonify({
                    "success": True,
                    "message": f"任务 {task_id} 的日志已清空"
                })
            else:
                # 创建空日志文件
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, 'w') as f:
                    pass
                
                # 写入一条初始日志，表示日志已创建
                task_logger = LoggerHelper.get_task_logger(task_id)
                task_logger.info("日志文件已创建，等待新日志...")
                
                # 记录到系统日志
                sys_logger = LoggerHelper.get_system_logger("logger_helper")
                sys_logger.info(f"任务 {task_id} 的日志文件已创建")
                
                return jsonify({
                    "success": True,
                    "message": f"任务 {task_id} 的日志文件已创建"
                })
                
        except Exception as e:
            # 记录错误到系统日志
            sys_logger = LoggerHelper.get_system_logger("logger_helper")
            sys_logger.error(f"清空任务 {task_id} 日志失败: {str(e)}")
            
            return jsonify({
                "success": False,
                "message": f"清空日志失败: {str(e)}"
            }), 500