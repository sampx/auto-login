
import os
import signal
import sys
import logging
from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS
from dotenv import load_dotenv

from logger_helper import setup_logging
from scheduler_engine import SchedulerEngine

# --- Blueprints ---
from api_blueprint import api_bp, init_scheduler_engine

# --- Initial Setup ---
load_dotenv()
# Configure logging at the very beginning
setup_logging()

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Logger Configuration ---
logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def init_services():
    """Initializes all background services and engines."""
    global scheduler_engine
    logger.info("开始初始化所有后台服务...")
    
    # Initialize new scheduler engine (NEW VERSION - for new features)
    scheduler_engine = SchedulerEngine()
    scheduler_engine.start()
    
    # Pass the initialized engine to the blueprint
    with app.app_context():
        init_scheduler_engine(scheduler_engine)
    
    logger.info("所有后台服务初始化完成。")

# --- Register Blueprints ---
app.register_blueprint(api_bp)

# --- Core Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# --- Signal Handling and Cleanup ---
def cleanup():
    logger.info("开始清理资源...")
    if 'scheduler_engine' in globals() and scheduler_engine:
        scheduler_engine.stop()
    logger.info("资源清理完成。")

def signal_handler(signum, frame):
    signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logger.info(f"接收到 {signal_name} 信号，准备关闭服务...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# --- Main Execution ---
if __name__ == '__main__':
    try:
        # Initialize services only once to prevent duplicate initialization
        init_services()
        
        port = int(os.getenv('WEB_PORT', 5001))
        # Determine Flask debug mode based on LOG_LEVEL, but disable reloader to prevent double initialization
        flask_debug_mode = (os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG')
        logger.info(f"启动Web服务器在端口 {port} (调试模式: {flask_debug_mode})...")
        
        # Always disable reloader to prevent double initialization of services
        app.run(host='0.0.0.0', port=port, debug=flask_debug_mode, use_reloader=False)
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
    finally:
        cleanup()
