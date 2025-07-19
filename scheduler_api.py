#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务调度API接口
提供RESTful API用于管理通用任务调度引擎
"""

import os
import json
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from scheduler_engine import SchedulerEngine, Task
from dataclasses import asdict
from apscheduler.triggers.cron import CronTrigger

# 创建Flask应用
app = Flask(__name__)

# 启用CORS支持
CORS(app)

# 全局调度引擎实例
scheduler_engine = None

def init_scheduler():
    """初始化调度引擎"""
    global scheduler_engine
    if scheduler_engine is None:
        scheduler_engine = SchedulerEngine()
        scheduler_engine.start()
    return scheduler_engine

# 路由：首页
@app.route('/')
def index():
    """渲染调度任务管理页面"""
    return render_template('scheduler.html')

# API路由：获取所有任务
@app.route('/api/scheduler/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务列表"""
    try:
        engine = init_scheduler()
        tasks = engine.get_tasks()
        return jsonify({
            "success": True,
            "data": tasks,
            "total": len(tasks)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：获取单个任务
@app.route('/api/scheduler/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取指定任务详情"""
    try:
        init_scheduler()
        task = scheduler_engine.get_task(task_id)
        if task:
            return jsonify({
                "success": True,
                "data": task
            })
        else:
            return jsonify({
                "success": False,
                "message": f"任务 {task_id} 不存在"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：创建新任务
@app.route('/api/scheduler/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        init_scheduler()
        data = request.json
        
        # 验证必填字段
        required_fields = ['task_id', 'task_name', 'task_exec', 'task_schedule']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }), 400
        
        # 创建任务对象
        task = Task(
            task_id=data['task_id'],
            task_name=data['task_name'],
            task_desc=data.get('task_desc', ''),
            task_exec=data['task_exec'],
            task_schedule=data['task_schedule'],
            task_timeout=data.get('task_timeout'),
            task_retry=data.get('task_retry', 0),
            task_retry_interval=data.get('task_retry_interval', 60),
            task_enabled=data.get('task_enabled', True),
            task_log=data.get('task_log'),
            task_env=data.get('task_env', {}),
            task_dependencies=data.get('task_dependencies', []),
            task_notify=data.get('task_notify', {})
        )
        
        # 验证任务执行文件是否存在（支持命令行格式）
        exec_path = task.task_exec
        if task.task_exec.startswith('python '):
            # 提取Python脚本路径
            parts = task.task_exec.split(' ', 1)
            if len(parts) > 1:
                exec_path = parts[1].split()[0]  # 处理带参数的情况
        
        # 只检查.py文件
        if exec_path.endswith('.py') and not os.path.exists(exec_path):
            return jsonify({
                "success": False,
                "message": f"任务执行文件不存在: {exec_path}"
            }), 400
        
        # 添加任务
        if scheduler_engine.add_task(task):
            return jsonify({
                "success": True,
                "message": "任务创建成功",
                "data": asdict(task)
            })
        else:
            return jsonify({
                "success": False,
                "message": "任务已存在"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：更新任务
@app.route('/api/scheduler/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务配置"""
    try:
        init_scheduler()
        data = request.json
        
        # 创建新任务对象
        task = Task(
            task_id=task_id,
            task_name=data['task_name'],
            task_desc=data.get('task_desc', ''),
            task_exec=data['task_exec'],
            task_schedule=data['task_schedule'],
            task_timeout=data.get('task_timeout'),
            task_retry=data.get('task_retry', 0),
            task_retry_interval=data.get('task_retry_interval', 60),
            task_enabled=data.get('task_enabled', True),
            task_log=data.get('task_log'),
            task_env=data.get('task_env', {}),
            task_dependencies=data.get('task_dependencies', []),
            task_notify=data.get('task_notify', {})
        )
        
        # 验证任务执行文件是否存在（支持命令行格式）
        exec_path = task.task_exec
        if task.task_exec.startswith('python '):
            # 提取Python脚本路径
            parts = task.task_exec.split(' ', 1)
            if len(parts) > 1:
                exec_path = parts[1].split()[0]  # 处理带参数的情况
        
        # 只检查.py文件
        if exec_path.endswith('.py') and not os.path.exists(exec_path):
            return jsonify({
                "success": False,
                "message": f"任务执行文件不存在: {exec_path}"
            }), 400
        
        # 更新任务
        if scheduler_engine.update_task(task):
            return jsonify({
                "success": True,
                "message": "任务更新成功",
                "data": asdict(task)
            })
        else:
            return jsonify({
                "success": False,
                "message": "任务更新失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：启用/禁用任务
@app.route('/api/scheduler/tasks/<task_id>/toggle', methods=['POST'])
def toggle_task_enabled(task_id):
    """启用或禁用任务"""
    try:
        init_scheduler()
        
        data = request.json or {}
        enabled = data.get('enabled', True)
        
        # 使用scheduler_engine的toggle_task方法
        if scheduler_engine.toggle_task(task_id, enabled):
            return jsonify({
                "success": True,
                "message": f"任务已{'启用' if enabled else '禁用'}",
                "data": {
                    "task_id": task_id,
                    "enabled": enabled
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": f"任务 {task_id} 不存在或状态更新失败"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：删除任务
@app.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        init_scheduler()
        
        if scheduler_engine.remove_task(task_id):
            return jsonify({
                "success": True,
                "message": "任务删除成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "任务不存在"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：手动触发任务执行
@app.route('/api/scheduler/tasks/<task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """手动触发任务执行"""
    try:
        engine = init_scheduler()
        
        if engine.execute_task_manually(task_id):
            return jsonify({
                "success": True,
                "message": f"任务 {task_id} 已加入执行队列"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"任务 {task_id} 不存在或执行失败"
            }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：验证cron表达式
@app.route('/api/scheduler/validate-cron', methods=['POST'])
def validate_cron():
    """验证cron表达式"""
    try:
        data = request.json
        cron_expr = data.get('cron')
        
        if not cron_expr:
            return jsonify({
                "success": False,
                "message": "缺少cron表达式"
            }), 400
        
        try:
            trigger = CronTrigger.from_crontab(cron_expr)
            next_run = trigger.get_next_fire_time(None, datetime.now())
            
            return jsonify({
                "success": True,
                "data": {
                    "valid": True,
                    "next_run": next_run.isoformat() if next_run else None,
                    "expression": cron_expr
                }
            })
        except Exception as e:
            return jsonify({
                "success": True,
                "data": {
                    "valid": False,
                    "error": str(e)
                }
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：获取任务日志
@app.route('/api/scheduler/tasks/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """获取任务日志"""
    try:
        init_scheduler()
        
        # 获取任务配置
        task = scheduler_engine.get_task(task_id)
        if not task:
            return jsonify({
                "success": False,
                "message": f"任务 {task_id} 不存在"
            }), 404
        
        log_file = task.get('task_log', f'logs/task_{task_id}.log')
        
        if not os.path.exists(log_file):
            return jsonify({
                "success": True,
                "data": [],
                "message": "暂无日志"
            })
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 获取最后100行
            lines = lines[-100:] if len(lines) > 100 else lines
            
            return jsonify({
                "success": True,
                "data": [{
                    "line": i + 1,
                    "content": line.strip()
                } for i, line in enumerate(lines)]
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"读取日志失败: {e}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API路由：清空任务日志
@app.route('/api/scheduler/tasks/<task_id>/logs/clear', methods=['POST'])
def clear_task_logs(task_id):
    """清空指定任务的日志文件"""
    try:
        engine = init_scheduler()
        task = engine.get_task(task_id)
        if not task:
            return jsonify({"success": False, "message": "任务不存在"}), 404

        log_file = task.get('task_log', f'logs/task_{task_id}.log')
        if os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.truncate(0)
            return jsonify({"success": True, "message": "日志已清空"})
        else:
            return jsonify({"success": True, "message": "日志文件不存在"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 静态文件路由
@app.route('/scheduler/static/<path:path>')
def send_static(path):
    """提供静态文件"""
    return send_from_directory('static', path)

# 初始化调度引擎
with app.app_context():
    init_scheduler()

# 信号处理器
def signal_handler(signum, frame):
    """处理终止信号"""
    print(f"\n收到信号 {signum}，正在停止...")
    if scheduler_engine:
        scheduler_engine.stop()
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    try:
        init_scheduler()
        app.run(host='0.0.0.0', port=5002, debug=False)
    except Exception as e:
        print(f"启动失败: {e}")
        if scheduler_engine:
            scheduler_engine.stop()