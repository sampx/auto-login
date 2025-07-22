
import logging
from flask import Blueprint, jsonify
from task_manager import get_task_manager

legacy_api_bp = Blueprint('legacy_api_bp', __name__)

logger = logging.getLogger(__name__)
task_manager = get_task_manager()

@legacy_api_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    try:
        tasks = task_manager.get_tasks()
        logger.info(f"旧版API: 成功获取任务列表，共 {len(tasks)} 个任务")
        return jsonify({"success": True, "tasks": tasks})
    except Exception as e:
        logger.error(f"旧版API: 获取任务列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@legacy_api_bp.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取指定任务的详情"""
    try:
        task = task_manager.get_task(task_id)
        if task:
            logger.info(f"旧版API: 成功获取任务 {task_id} 的详情")
            return jsonify({"success": True, "task": task})
        else:
            logger.warning(f"旧版API: 获取任务 {task_id} 详情失败，任务不存在")
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在"}), 404
    except Exception as e:
        logger.error(f"旧版API: 获取任务详情时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@legacy_api_bp.route('/api/tasks/<task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动指定任务"""
    try:
        logger.info(f"旧版API: 收到启动任务 {task_id} 的请求")
        result = task_manager.start_task(task_id)
        if result["success"]:
            logger.info(f"旧版API: 任务 {task_id} 启动成功")
            return jsonify(result)
        else:
            logger.warning(f"旧版API: 任务 {task_id} 启动失败: {result.get('message', '未知原因')}")
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"旧版API: 启动任务时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@legacy_api_bp.route('/api/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止指定任务"""
    try:
        logger.info(f"旧版API: 收到停止任务 {task_id} 的请求")
        result = task_manager.stop_task(task_id)
        if result["success"]:
            logger.info(f"旧版API: 任务 {task_id} 停止成功")
            return jsonify(result)
        else:
            logger.warning(f"旧版API: 任务 {task_id} 停止失败: {result.get('message', '未知原因')}")
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"旧版API: 停止任务时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@legacy_api_bp.route('/api/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """获取指定任务的状态"""
    try:
        result = task_manager.get_task_status(task_id)
        if result["success"]:
            return jsonify(result)
        else:
            logger.warning(f"旧版API: 获取任务 {task_id} 状态失败，任务不存在")
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"旧版API: 获取任务状态时发生异常: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
