import os
import signal
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv, set_key
from task_manager import get_task_manager
from logger_helper import LoggerHelper, add_log_routes

# 创建Flask应用
app = Flask(__name__)
ENV_FILE_PATH = '.env'

# 禁用Flask默认的访问日志
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # 只显示错误级别的日志

# 加载现有的环境变量
load_dotenv(ENV_FILE_PATH)

# 获取系统日志记录器 - 同时输出到控制台和系统日志文件
logger = LoggerHelper.get_system_logger(__name__)

# 获取任务管理器
task_manager = get_task_manager()

# 添加日志查看API路由
add_log_routes(app)

# 主页路由
@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

# API路由 - 获取任务列表
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    try:
        tasks = task_manager.get_tasks()
        logger.info(f"API调用: 获取任务列表，返回{len(tasks)}个任务")
        return jsonify({"success": True, "tasks": tasks})
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# API路由 - 获取任务详情
@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取指定任务的详情"""
    try:
        task = task_manager.get_task(task_id)
        if task:
            logger.info(f"API调用: 获取任务 {task_id} 详情")
            return jsonify({"success": True, "task": task})
        else:
            logger.warning(f"API调用: 获取任务 {task_id} 详情失败，任务不存在")
            return jsonify({"success": False, "message": f"任务 {task_id} 不存在"}), 404
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# API路由 - 启动任务
@app.route('/api/tasks/<task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动指定任务"""
    try:
        logger.info(f"API调用: 启动任务 {task_id}")
        result = task_manager.start_task(task_id)
        if result["success"]:
            logger.info(f"任务 {task_id} 启动成功")
            return jsonify(result)
        else:
            logger.warning(f"任务 {task_id} 启动失败: {result.get('message', '未知原因')}")
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"启动任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# API路由 - 停止任务
@app.route('/api/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止指定任务"""
    try:
        logger.info(f"API调用: 停止任务 {task_id}")
        result = task_manager.stop_task(task_id)
        if result["success"]:
            logger.info(f"任务 {task_id} 停止成功")
            return jsonify(result)
        else:
            logger.warning(f"任务 {task_id} 停止失败: {result.get('message', '未知原因')}")
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"停止任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# API路由 - 获取任务状态
@app.route('/api/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """获取指定任务的状态"""
    try:
        result = task_manager.get_task_status(task_id)
        if result["success"]:
            return jsonify(result)
        else:
            logger.warning(f"API调用: 获取任务 {task_id} 状态失败，任务不存在")
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# API路由 - 获取系统配置
@app.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    try:
        # 从环境变量中读取配置
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
        
        # 隐藏密码
        if config["PASSWORD"]:
            config["PASSWORD"] = "********"
        
        logger.info("API调用: 获取系统配置")
        return jsonify({"success": True, "config": config})
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# API路由 - 更新系统配置
@app.route('/api/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        # 获取请求数据
        data = request.json
        if not data:
            logger.warning("API调用: 更新配置失败，无效的请求数据")
            return jsonify({"success": False, "message": "无效的请求数据"}), 400
            
        # 允许更新的配置项
        allowed_keys = [
            "WEBSITE_URL", "USERNAME", "PASSWORD", "MAX_RETRIES",
            "LOGIN_SCHEDULE_TYPE", "LOGIN_SCHEDULE_DATE", "LOGIN_SCHEDULE_TIME",
            "LOG_LEVEL"
        ]
        
        # 验证配置
        for key, value in data.items():
            if key not in allowed_keys:
                logger.warning(f"API调用: 更新配置失败，不允许更新配置项: {key}")
                return jsonify({"success": False, "message": f"不允许更新配置项: {key}"}), 400
        
        logger.info("API调用: 更新系统配置")
        
        # 更新环境变量文件
        for key, value in data.items():
            if value is not None:
                set_key(ENV_FILE_PATH, key, value)
                if key != "PASSWORD":  # 不记录密码
                    logger.info(f"配置项 {key} 已更新")
                else:
                    logger.info(f"配置项 PASSWORD 已更新")
                
        # 重新加载环境变量
        load_dotenv(ENV_FILE_PATH, override=True)
        
        logger.info("系统配置已成功更新")
        return jsonify({"success": True, "message": "配置已更新"})
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# 静态文件路由
@app.route('/static/<path:path>')
def send_static(path):
    """提供静态文件"""
    return send_from_directory('static', path)

# 应用启动和清理
def cleanup():
    """清理资源"""
    logger.info("正在清理资源...")
    task_manager.cleanup()
    logger.info("资源清理完成")

# 信号处理
def signal_handler(signum, frame):
    """处理终止信号"""
    signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logger.info(f"收到{signal_name}信号，正在停止...")
    cleanup()
    logger.info("程序已停止")
    os._exit(0)

# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 主函数
if __name__ == '__main__':
    try:
        # 从环境变量获取端口，默认5001
        port = int(os.getenv('WEB_PORT', 5001))
        logger.info(f"启动Web任务管理器...端口: {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Web任务管理器启动失败: {str(e)}")
    finally:
        cleanup()