
import os
import logging
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, set_key
from scheduler_engine import SchedulerEngine, Task
from dataclasses import asdict
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

api_bp = Blueprint('api_bp', __name__)

logger = logging.getLogger(__name__)
ENV_FILE_PATH = '.env'

# This will be initialized by the main app
scheduler_engine = None

def init_scheduler_engine(engine: SchedulerEngine):
    global scheduler_engine
    scheduler_engine = engine

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
def create_task():
    """创建新任务"""
    try:
        data = request.json
        required_fields = ['task_id', 'task_name', 'task_exec', 'task_schedule']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400
        
        task = Task(**data)
        
        exec_path = task.task_exec
        if task.task_exec.startswith('python '):
            parts = task.task_exec.split(' ', 1)
            if len(parts) > 1:
                exec_path = parts[1].split()[0]
        
        if exec_path.endswith('.py') and not os.path.exists(exec_path):
            return jsonify({"success": False, "message": f"任务执行文件不存在: {exec_path}"}), 400
        
        if scheduler_engine.add_task(task):
            logger.info(f"API接口: 成功创建任务 {task.task_id}")
            return jsonify({"success": True, "message": "任务创建成功", "data": asdict(task)})
        else:
            logger.warning(f"API接口: 创建任务失败，因为任务 {task.task_id} 已存在")
            return jsonify({"success": False, "message": "任务已存在"}), 400
    except Exception as e:
        logger.error(f"API接口: 创建任务时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务配置"""
    try:
        # 从引擎中获取原始任务
        existing_task_dict = scheduler_engine.get_task(task_id)
        if not existing_task_dict:
            return jsonify({"success": False, "message": "任务不存在"}), 404

        # 将其转换为Task对象以便于更新
        # 过滤掉Task dataclass中不存在的字段，例如next_run_time
        from dataclasses import fields
        task_field_names = {f.name for f in fields(Task)}
        filtered_existing_task_dict = {k: v for k, v in existing_task_dict.items() if k in task_field_names}
        existing_task = Task(**filtered_existing_task_dict)

        # 获取请求数据并更新任务对象
        data = request.json
        for key, value in data.items():
            if hasattr(existing_task, key):
                setattr(existing_task, key, value)

        # 验证执行文件是否存在
        exec_path = existing_task.task_exec
        if existing_task.task_exec.startswith('python '):
            parts = existing_task.task_exec.split(' ', 1)
            if len(parts) > 1:
                exec_path = parts[1].split()[0]
        
        if exec_path.endswith('.py') and not os.path.exists(exec_path):
            return jsonify({"success": False, "message": f"任务执行文件不存在: {exec_path}"}), 400
        
        # 使用更新后的完整任务对象进行更新
        if scheduler_engine.update_task(existing_task):
            logger.info(f"API接口: 成功更新任务 {task_id}")
            return jsonify({"success": True, "message": "任务更新成功", "data": asdict(existing_task)})
        else:
            logger.warning(f"API接口: 更新任务 {task_id} 失败")
            return jsonify({"success": False, "message": "任务更新失败"}), 500
            
    except Exception as e:
        logger.error(f"API接口: 更新任务时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/toggle', methods=['POST'])
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
        if not os.path.exists(log_file):
            logger.debug(f"API接口: 任务 {task_id} 的日志文件不存在")
            return jsonify({"success": True, "data": [], "message": "暂无日志"})
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        lines = lines[-100:]
        logger.debug(f"API接口: 成功获取任务 {task_id} 的日志")
        return jsonify({"success": True, "data": [{"line": i + 1, "content": line.strip()} for i, line in enumerate(lines)]})
    except Exception as e:
        logger.error(f"API接口: 读取任务 {task_id} 日志时发生异常: {e}")
        return jsonify({"success": False, "message": f"读取日志失败: {e}"}), 500

@api_bp.route('/api/scheduler/tasks/<task_id>/logs/clear', methods=['POST'])
def clear_task_logs(task_id):
    """清空指定任务的日志文件"""
    try:
        task = scheduler_engine.get_task(task_id)
        if not task:
            logger.warning(f"API接口: 清空任务 {task_id} 日志失败，任务不存在")
            return jsonify({"success": False, "message": "任务不存在"}), 404

        log_file = task.get('task_log', f'logs/task_{task_id}.log')
        if os.path.exists(log_file):
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

# --- Log Viewer API ---
# Note: This is a simplified version. The original add_log_routes might have more logic.
@api_bp.route('/api/tasks/<task_id>/logs', methods=['GET'])
def get_legacy_task_logs(task_id):
    from task_manager import get_task_manager
    task_manager = get_task_manager()
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    result = task_manager.get_task_logs(task_id, limit=limit, offset=offset)
    if not result["success"]:
        logger.error(f"API接口: 获取旧版任务 {task_id} 日志失败: {result.get('message', '未知错误')}")
    return jsonify(result)

@api_bp.route('/api/tasks/<task_id>/logs/clear', methods=['POST'])
def clear_legacy_task_logs(task_id):
    log_file = f'logs/task_{task_id}.log'
    if os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.truncate(0)
        logger.info(f"API接口: 成功清空旧版任务 {task_id} 的日志")
        return jsonify({"success": True, "message": "日志已清空"})
    logger.info(f"API接口: 旧版任务 {task_id} 的日志文件不存在，无需清空")
    return jsonify({"success": True, "message": "日志文件不存在"})
