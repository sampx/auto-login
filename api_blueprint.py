import os
import logging
import time
import json
import threading
import hashlib
import fcntl
import shutil
import tempfile
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, set_key
from scheduler_engine import SchedulerEngine, Task
from dataclasses import asdict
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from functools import wraps

api_bp = Blueprint('api_bp', __name__)

logger = logging.getLogger(__name__)
ENV_FILE_PATH = '.env'

# 任务锁目录
LOCKS_DIR = 'locks'
if not os.path.exists(LOCKS_DIR):
    os.makedirs(LOCKS_DIR, exist_ok=True)

# 任务操作锁
task_locks = {}

# This will be initialized by the main app
scheduler_engine = None

def init_scheduler_engine(engine: SchedulerEngine):
    global scheduler_engine
    scheduler_engine = engine
    
def acquire_task_lock(task_id, timeout=10):
    """获取任务操作锁，防止并发操作同一任务"""
    lock_file = os.path.join(LOCKS_DIR, f"{task_id}.lock")
    start_time = time.time()
    
    # 确保锁目录存在
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    
    try:
        # 创建或打开锁文件
        fd = open(lock_file, 'w+')
        
        while True:
            try:
                # 尝试获取文件锁
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # 成功获取锁
                task_locks[task_id] = fd
                return fd
            except IOError:
                # 锁被其他进程持有
                if time.time() - start_time > timeout:
                    fd.close()
                    raise TimeoutError(f"获取任务 {task_id} 的锁超时")
                # 等待一段时间后重试
                time.sleep(0.1)
    except Exception as e:
        logger.error(f"获取任务 {task_id} 的锁失败: {e}")
        raise
        
def release_task_lock(task_id):
    """释放任务操作锁"""
    if task_id in task_locks:
        try:
            fd = task_locks[task_id]
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()
            del task_locks[task_id]
            return True
        except Exception as e:
            logger.error(f"释放任务 {task_id} 的锁失败: {e}")
    return False

def with_task_lock(func):
    """任务锁装饰器，确保同一时间只有一个请求可以操作指定任务"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        task_id = kwargs.get('task_id')
        if not task_id:
            # 如果没有task_id参数，尝试从URL路径中提取
            if len(args) > 0 and isinstance(args[0], str):
                task_id = args[0]

        if not task_id and request.is_json:
            data = request.get_json(silent=True) or {}
            task_id = data.get('task_id')

        if not task_id:
            return func(*args, **kwargs)

        lock_acquired = False
        try:
            # 尝试获取锁
            acquire_task_lock(task_id)
            lock_acquired = True
            return func(*args, **kwargs)
        except TimeoutError:
            logger.warning(f"API接口: 任务 {task_id} 正在被其他请求处理，请稍后重试")
            return jsonify({"success": False, "message": "任务正在被其他请求处理，请稍后重试"}), 423
        finally:
            if lock_acquired:
                release_task_lock(task_id)
    return wrapper

class TransactionManager:
    """事务管理器，用于确保文件操作的原子性"""
    
    def __init__(self, task_id):
        self.task_id = task_id
        self.task_dir = os.path.join("tasks", task_id)
        self.backup_dir = None
        self.operations = []
        self.success = False
        
    def __enter__(self):
        """开始事务"""
        # 创建临时备份目录
        if os.path.exists(self.task_dir):
            self.backup_dir = tempfile.mkdtemp(prefix=f"task_{self.task_id}_backup_")
            # 复制任务目录内容到备份目录
            if os.path.exists(self.task_dir):
                for item in os.listdir(self.task_dir):
                    src = os.path.join(self.task_dir, item)
                    dst = os.path.join(self.backup_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """结束事务，如果有异常则回滚"""
        if exc_type is not None:
            # 发生异常，回滚操作
            self.rollback()
            return False
        
        # 标记事务成功
        self.success = True
        
        # 清理备份
        if self.backup_dir and os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
        
        return True
    
    def rollback(self):
        """回滚所有操作"""
        if not self.backup_dir or not os.path.exists(self.backup_dir):
            logger.warning(f"API接口: 无法回滚任务 {self.task_id} 的操作，备份目录不存在")
            return False
            
        try:
            # 删除当前任务目录
            if os.path.exists(self.task_dir):
                shutil.rmtree(self.task_dir)
                
            # 从备份恢复
            shutil.copytree(self.backup_dir, self.task_dir)
            
            # 清理备份
            shutil.rmtree(self.backup_dir)
            
            logger.info(f"API接口: 成功回滚任务 {self.task_id} 的操作")
            return True
        except Exception as e:
            logger.error(f"API接口: 回滚任务 {self.task_id} 的操作失败: {e}")
            return False
    
    def add_operation(self, operation):
        """记录操作"""
        self.operations.append(operation)

# 日志文件管理
class LogManager:
    """日志文件管理器，处理日志轮转和大小限制"""
    
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 默认最大日志大小为10MB
    MAX_LOG_FILES = 5  # 默认最多保留5个历史日志文件
    
    @staticmethod
    def check_and_rotate_log(log_file, max_size=None, max_files=None):
        """检查日志文件大小，如果超过限制则进行轮转"""
        if not os.path.exists(log_file):
            return
            
        if max_size is None:
            max_size = LogManager.MAX_LOG_SIZE
            
        if max_files is None:
            max_files = LogManager.MAX_LOG_FILES
            
        # 检查文件大小
        file_size = os.path.getsize(log_file)
        if file_size <= max_size:
            return
            
        # 需要轮转日志
        logger.info(f"日志文件 {log_file} 大小 ({file_size} 字节) 超过限制 ({max_size} 字节)，开始轮转")
        
        # 删除最老的日志文件（如果存在）
        oldest_log = f"{log_file}.{max_files}"
        if os.path.exists(oldest_log):
            try:
                os.remove(oldest_log)
                logger.debug(f"已删除最老的日志文件: {oldest_log}")
            except Exception as e:
                logger.error(f"删除日志文件 {oldest_log} 失败: {e}")
        
        # 轮转现有的日志文件
        for i in range(max_files - 1, 0, -1):
            old_log = f"{log_file}.{i}"
            new_log = f"{log_file}.{i + 1}"
            if os.path.exists(old_log):
                try:
                    shutil.move(old_log, new_log)
                    logger.debug(f"轮转日志文件: {old_log} -> {new_log}")
                except Exception as e:
                    logger.error(f"轮转日志文件 {old_log} 失败: {e}")
        
        # 轮转当前日志文件
        try:
            shutil.copy2(log_file, f"{log_file}.1")
            with open(log_file, 'w') as f:
                f.truncate(0)
            logger.info(f"成功轮转日志文件 {log_file}")
        except Exception as e:
            logger.error(f"轮转当前日志文件 {log_file} 失败: {e}")
    
    @staticmethod
    def get_log_content(log_file, limit=100, offset=0):
        """获取日志内容，支持分页"""
        if not os.path.exists(log_file):
            return []
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 计算总行数
            total_lines = len(lines)
            
            # 如果offset为负数，表示从末尾开始计算
            if offset < 0:
                offset = max(0, total_lines + offset)
            
            # 确保offset在有效范围内
            offset = min(offset, total_lines)
            
            # 获取指定范围的行
            selected_lines = lines[offset:offset + limit]
            
            return [{"line": offset + i + 1, "content": line.strip()} for i, line in enumerate(selected_lines)]
        except Exception as e:
            logger.error(f"读取日志文件 {log_file} 失败: {e}")
            return []

# --- System Config API ---

@api_bp.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    try:
        config = {
            "WEBSITE_URL": os.getenv("WEBSITE_URL", ""),
            "USERNAME": os.getenv("USERNAME", ""),
            "PASSWORD": os.getenv("PASSWORD", ""),
            "MAX_RETRIES": os.getenv("MAX_RETRIES", ""),
            "LOGIN_SCHEDULE_TYPE": os.getenv("LOGIN_SCHEDULE_TYPE", ""),
            "LOGIN_SCHEDULE_DATE": os.getenv("LOGIN_SCHEDULE_DATE", ""),
            "LOGIN_SCHEDULE_TIME": os.getenv("LOGIN_SCHEDULE_TIME", ""),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "")
        }
        if config["PASSWORD"]:
            config["PASSWORD"] = "********"
        logger.info("API接口: 成功获取系统配置")
        return jsonify({"success": True, "config": config})
    except Exception as e:
        logger.error(f"API接口: 获取系统配置失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "无效的请求数据"}), 400
        
        allowed_keys = [
            "WEBSITE_URL", "USERNAME", "PASSWORD", "MAX_RETRIES",
            "LOGIN_SCHEDULE_TYPE", "LOGIN_SCHEDULE_DATE", "LOGIN_SCHEDULE_TIME",
            "LOG_LEVEL"
        ]
        
        for key, value in data.items():
            if key not in allowed_keys:
                return jsonify({"success": False, "message": f"不允许更新配置项: {key}"}), 400
        
        logger.info("API接口: 成功更新系统配置")
        return jsonify({"success": True, "message": "配置已更新"})
    except Exception as e:
        logger.error(f"API接口: 更新系统配置失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# --- Scheduler Engine API ---

@api_bp.route('/api/scheduler/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务列表"""
    logger.debug("API接口: 收到获取所有任务列表的请求")
    try:
        tasks = scheduler_engine.get_tasks()
        logger.debug(f"API接口: 成功获取所有任务，共 {len(tasks)} 个")
        return jsonify({"success": True, "data": tasks, "total": len(tasks)})
    except Exception as e:
        logger.error(f"API接口: 获取所有任务列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取指定任务详情"""
    try:
        task = scheduler_engine.get_task(task_id)
        if task:
            return jsonify({"success": True, "data": task})
        else:
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks', methods=['POST'])
@with_task_lock
def create_task():
    """创建新任务"""
    try:
        data = request.json
        required_fields = ['task_id', 'task_name', 'task_schedule']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400
        
        task_id = data['task_id']
        
        # 验证任务ID格式
        if not task_id.isalnum() and not all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in task_id):
            return jsonify({"success": False, "message": "任务ID只能包含字母、数字、下划线和连字符"}), 400
        
        # 先检查任务是否已存在
        if scheduler_engine.get_task(task_id):
            logger.warning(f"API接口: 创建任务失败，因为任务 {task_id} 已存在")
            return jsonify({"success": False, "message": f"任务ID '{task_id}' 已存在，请使用其他ID"}), 400
            
        script_type = data.get('script_type', 'python')  # 默认为python
        
        # 使用事务管理器确保操作的原子性
        with TransactionManager(task_id) as transaction:
            # 确定任务目录路径
            task_dir = os.path.join("tasks", task_id)
            
            # 确定脚本文件名和执行命令
            if script_type == "python":
                script_name = f"{task_id}.py"
                task_exec = f"python {script_name}"
            else:
                script_name = f"{task_id}.sh"
                task_exec = f"bash {script_name}"
            
            # 添加执行命令到数据中
            data['task_exec'] = task_exec
            
            # 移除script_type字段，因为Task类不接受这个参数
            if 'script_type' in data:
                del data['script_type']
            
            # 创建Task对象
            task = Task(**data)
            
            # 创建任务目录
            if not os.path.exists(task_dir):
                os.makedirs(task_dir, exist_ok=True)
                logger.info(f"API接口: 成功创建任务目录 {task_dir}")
            
            # 确定模板文件路径
            if script_type == "python":
                template_path = "templates/task/python_template.py"
            else:
                template_path = "templates/task/shell_template.sh"
            
            # 目标脚本文件路径
            script_path = os.path.join(task_dir, script_name)
            
            # 如果脚本文件不存在，则从模板创建
            if not os.path.exists(script_path):
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as src_file:
                        template_content = src_file.read()
                        
                    with open(script_path, 'w', encoding='utf-8') as dest_file:
                        dest_file.write(template_content)
                        
                    # 如果是shell脚本，设置执行权限
                    if script_type == "shell":
                        os.chmod(script_path, 0o755)
                        
                    logger.info(f"API接口: 成功创建任务脚本文件 {script_path}")
                else:
                    logger.warning(f"API接口: 模板文件 {template_path} 不存在，无法创建脚本文件")
                    return jsonify({"success": False, "message": f"模板文件 {template_path} 不存在"}), 404
            
            # 创建或更新config.json文件
            config_path = os.path.join(task_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as config_file:
                json.dump(asdict(task), config_file, indent=2, ensure_ascii=False)
                
            logger.info(f"API接口: 成功创建任务配置文件 {config_path}")
            
            # 添加任务到调度引擎
            if scheduler_engine.add_task(task):
                logger.info(f"API接口: 成功创建任务 {task.task_id}")
                return jsonify({
                    "success": True, 
                    "message": "任务创建成功", 
                    "data": asdict(task)
                })
            else:
                # 这种情况理论上不应该发生，因为我们已经在前面检查了任务是否存在
                # 但为了健壮性，我们仍然处理这种情况
                logger.warning(f"API接口: 创建任务失败，因为任务 {task.task_id} 已存在")
                return jsonify({"success": False, "message": "任务已存在"}), 400
    except Exception as e:
        logger.error(f"API接口: 创建任务时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>', methods=['PUT'])
@with_task_lock
def update_task(task_id):
    """更新任务配置"""
    # 防止重复更新请求的简单机制
    request_id = request.headers.get('X-Request-ID', '')
    
    # 使用线程本地存储来跟踪最近处理的请求
    if not hasattr(update_task, '_last_requests'):
        update_task._last_requests = {}
    
    # 如果是重复请求，直接返回成功
    if request_id and request_id in update_task._last_requests:
        last_time = update_task._last_requests[request_id]
        if time.time() - last_time < 2.0:  # 2秒内的重复请求
            logger.debug(f"API接口: 检测到重复更新请求 {request_id}，已忽略")
            return jsonify({"success": True, "message": "任务更新成功（重复请求）"})
    
    try:
        # 从引擎中获取原始任务
        existing_task_dict = scheduler_engine.get_task(task_id)
        if not existing_task_dict:
            return jsonify({"success": False, "message": "任务不存在"}), 404

        # 使用事务管理器确保操作的原子性
        with TransactionManager(task_id) as transaction:
            # 将其转换为Task对象以便于更新
            # 过滤掉Task dataclass中不存在的字段，例如next_run_time
            from dataclasses import fields
            task_field_names = {f.name for f in fields(Task)}
            filtered_existing_task_dict = {k: v for k, v in existing_task_dict.items() if k in task_field_names}
            existing_task = Task(**filtered_existing_task_dict)

            # 获取请求数据
            data = request.json
            
            # 防止修改任务ID
            if 'task_id' in data and data['task_id'] != task_id:
                logger.warning(f"API接口: 尝试修改任务ID从 {task_id} 到 {data['task_id']}，已拒绝")
                return jsonify({"success": False, "message": "不允许修改任务ID"}), 400
                
            # 验证CRON表达式
            if 'task_schedule' in data and data['task_schedule'] != existing_task.task_schedule:
                try:
                    trigger = CronTrigger.from_crontab(data['task_schedule'])
                    next_run = trigger.get_next_fire_time(None, datetime.now())
                    if not next_run:
                        logger.warning(f"API接口: 无效的CRON表达式: {data['task_schedule']}")
                        return jsonify({"success": False, "message": f"无效的CRON表达式: {data['task_schedule']}"}), 400
                except Exception as e:
                    logger.warning(f"API接口: 无效的CRON表达式: {data['task_schedule']}, 错误: {e}")
                    return jsonify({"success": False, "message": f"无效的CRON表达式: {data['task_schedule']}, 错误: {e}"}), 400
            
            # 更新任务对象
            for key, value in data.items():
                if hasattr(existing_task, key):
                    setattr(existing_task, key, value)

            # 验证执行文件是否存在（在任务目录内）
            task_dir = os.path.join("tasks", task_id)
            exec_path = existing_task.task_exec
            
            # 提取执行文件路径
            if existing_task.task_exec.startswith('python '):
                parts = existing_task.task_exec.split(' ', 1)
                if len(parts) > 1:
                    exec_path = parts[1].split()[0]
            elif existing_task.task_exec.startswith('bash '):
                parts = existing_task.task_exec.split(' ', 1)
                if len(parts) > 1:
                    exec_path = parts[1].split()[0]
            
            # 验证执行文件存在
            if exec_path.endswith('.py') or exec_path.endswith('.sh'):
                full_exec_path = os.path.join(task_dir, exec_path)
                if not os.path.exists(full_exec_path):
                    logger.warning(f"API接口: 任务执行文件不存在: {full_exec_path}")
                    return jsonify({"success": False, "message": f"任务执行文件不存在: {full_exec_path}"}), 400
            
            # 验证超时时间和重试次数
            if existing_task.task_timeout is not None and existing_task.task_timeout <= 0:
                logger.warning(f"API接口: 无效的超时时间: {existing_task.task_timeout}")
                return jsonify({"success": False, "message": "超时时间必须大于0"}), 400
                
            if existing_task.task_retry < 0:
                logger.warning(f"API接口: 无效的重试次数: {existing_task.task_retry}")
                return jsonify({"success": False, "message": "重试次数不能为负数"}), 400
                
            if existing_task.task_retry_interval <= 0:
                logger.warning(f"API接口: 无效的重试间隔: {existing_task.task_retry_interval}")
                return jsonify({"success": False, "message": "重试间隔必须大于0"}), 400
            
            # 更新配置文件
            config_path = os.path.join(task_dir, "config.json")
            try:
                with open(config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(asdict(existing_task), config_file, indent=2, ensure_ascii=False)
                logger.info(f"API接口: 成功更新任务配置文件 {config_path}")
            except Exception as e:
                logger.error(f"API接口: 更新任务配置文件失败: {e}")
                return jsonify({"success": False, "message": f"更新任务配置文件失败: {e}"}), 500
            
            # 使用更新后的完整任务对象进行更新
            if scheduler_engine.update_task(existing_task):
                logger.info(f"API接口: 成功更新任务 {task_id}")
                
                # 记录此请求已处理
                if request_id:
                    update_task._last_requests[request_id] = time.time()
                    # 清理旧请求记录
                    for old_id in list(update_task._last_requests.keys()):
                        if time.time() - update_task._last_requests[old_id] > 60:  # 60秒后清理
                            del update_task._last_requests[old_id]
                            
                return jsonify({"success": True, "message": "任务更新成功", "data": asdict(existing_task)})
            else:
                logger.warning(f"API接口: 更新任务 {task_id} 失败")
                return jsonify({"success": False, "message": "任务更新失败"}), 500
                
    except Exception as e:
        logger.error(f"API接口: 更新任务时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/toggle', methods=['POST'])
@with_task_lock
def toggle_task_enabled(task_id):
    """启用或禁用任务"""
    try:
        enabled = request.json.get('enabled', True)
        if scheduler_engine.toggle_task(task_id, enabled):
            logger.info(f"API接口: 任务 {task_id} 已切换为 {'启用' if enabled else '禁用'} 状态")
            return jsonify({"success": True, "message": f"任务已{'启用' if enabled else '禁用'}"})
        else:
            logger.warning(f"API接口: 切换任务 {task_id} 状态失败，任务不存在或更新操作未成功")
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在或状态更新失败"}), 404
    except Exception as e:
        logger.error(f"API接口: 切换任务 {task_id} 状态时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
@with_task_lock
def delete_task(task_id):
    """删除任务"""
    try:
        if scheduler_engine.remove_task(task_id):
            logger.info(f"API接口: 成功删除任务 {task_id}")
            return jsonify({"success": True, "message": "任务删除成功"})
        else:
            logger.warning(f"API接口: 删除任务 {task_id} 失败，任务不存在")
            return jsonify({"success": False, "message": "任务不存在"}), 404
    except Exception as e:
        logger.error(f"API接口: 删除任务 {task_id} 时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/execute', methods=['POST'])
@with_task_lock
def execute_task(task_id):
    """手动触发任务执行"""
    try:
        if scheduler_engine.execute_task_manually(task_id):
            logger.info(f"API接口: 已成功请求手动执行任务 {task_id}")
            return jsonify({"success": True, "message": f"任务 {task_id} 已加入执行队列"})
        else:
            logger.warning(f"API接口: 手动执行任务 {task_id} 失败，任务不存在")
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在或执行失败"}), 404
    except Exception as e:
        logger.error(f"API接口: 手动执行任务 {task_id} 时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/run-once', methods=['POST'])
@with_task_lock
def run_task_once(task_id):
    """直接运行一次任务"""
    try:
        if scheduler_engine.run_task_once(task_id):
            logger.info(f"API接口: 已成功请求运行一次任务 {task_id}")
            return jsonify({"success": True, "message": f"任务 {task_id} 开始执行"})
        else:
            logger.warning(f"API接口: 运行一次任务 {task_id} 失败，任务不存在")
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在或执行失败"}), 404
    except Exception as e:
        logger.error(f"API接口: 运行一次任务 {task_id} 时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/validate-cron', methods=['POST'])
def validate_cron():
    """验证cron表达式"""
    try:
        cron_expr = request.json.get('cron')
        if not cron_expr:
            logger.warning("API接口: CRON 表达式验证失败，请求中未提供表达式")
            return jsonify({"success": False, "message": "缺少cron表达式"}), 400
        
        try:
            trigger = CronTrigger.from_crontab(cron_expr)
            next_run = trigger.get_next_fire_time(None, datetime.now())
            logger.info(f"API接口: CRON 表达式 '{cron_expr}' 验证通过")
            return jsonify({"success": True, "data": {"valid": True, "next_run": next_run.isoformat() if next_run else None}})
        except Exception as e:
            logger.warning(f"API接口: CRON 表达式 '{cron_expr}' 验证失败: {e}")
            return jsonify({"success": True, "data": {"valid": False, "error": str(e)}})
    except Exception as e:
        logger.error(f"API接口: 验证 CRON 表达式时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """获取任务日志"""
    try:
        task = scheduler_engine.get_task(task_id)
        if not task:
            logger.warning(f"API接口: 获取任务 {task_id} 日志失败，任务不存在")
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在"}), 404
        
        log_file = task.get('task_log', f'logs/task_{task_id}.log')
        logger.debug(f"API接口: 尝试读取任务 {task_id} 的日志文件: {log_file}")
        
        # 检查并轮转日志文件
        LogManager.check_and_rotate_log(log_file)
        
        if not os.path.exists(log_file):
            logger.debug(f"API接口: 任务 {task_id} 的日志文件不存在")
            return jsonify({"success": True, "data": [], "message": "暂无日志", "log_file": log_file})
        
        # 获取分页参数
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 使用LogManager获取日志内容
        log_entries = LogManager.get_log_content(log_file, limit, offset)
        
        logger.debug(f"API接口: 成功获取任务 {task_id} 的日志")
        return jsonify({
            "success": True, 
            "data": log_entries, 
            "log_file": log_file,
            "has_more": os.path.getsize(log_file) > 0 and len(log_entries) == limit
        })
    except Exception as e:
        logger.error(f"API接口: 读取任务 {task_id} 日志时发生异常: {e}")
        return jsonify({"success": False, "message": f"读取日志失败: {e}"}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/logs/clear', methods=['POST'])
@with_task_lock
def clear_task_logs(task_id):
    """清空指定任务的日志文件"""
    try:
        task = scheduler_engine.get_task(task_id)
        if not task:
            logger.warning(f"API接口: 清空任务 {task_id} 日志失败，任务不存在")
            return jsonify({"success": False, "message": "任务不存在"}), 404

        log_file = task.get('task_log', f'logs/task_{task_id}.log')
        if os.path.exists(log_file):
            # 创建备份
            backup_file = f"{log_file}.bak"
            try:
                shutil.copy2(log_file, backup_file)
            except Exception as e:
                logger.warning(f"API接口: 创建日志备份失败: {e}")
            
            # 清空日志文件
            with open(log_file, 'w') as f:
                f.truncate(0)
            logger.info(f"API接口: 成功清空任务 {task_id} 的日志")
            return jsonify({"success": True, "message": "日志已清空"})
        else:
            logger.info(f"API接口: 任务 {task_id} 的日志文件不存在，无需清空")
            return jsonify({"success": True, "message": "日志文件不存在"})
    except Exception as e:
        logger.error(f"API接口: 清空任务 {task_id} 日志时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

