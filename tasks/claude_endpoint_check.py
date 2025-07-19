import os
import requests
import json
import logging
import sys
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_claude_endpoint():
    """测试Claude API端点"""
    logger.info("开始测试Claude API端点")
    
    # 从环境变量获取配置
    url = os.getenv("ANTHROPIC_BASE_URL")
    if url:
        url = url.rstrip('/') + "/v1/messages"
    api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")
    
    if not url or not api_key:
        logger.error("缺少必要的环境变量: ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_BASE_URL")
        return 2  # 系统异常：配置错误
    
    logger.info(f"使用端点: {url}")
    logger.info(f"API Key: {api_key[:4]}...{api_key[-4:]}")
    
    # 准备请求头和数据
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "请只回复我1个字谢谢"}
        ]
    }
    
    try:
        logger.info("发送请求到Claude API")
        start_time = datetime.now()
        
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"收到响应, 状态码: {response.status_code}, 耗时: {duration:.2f}秒")
        
        # 检查响应状态
        if response.status_code != 200:
            logger.error(f"请求失败, 状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}") # 打印完整响应内容
            return 1  # 业务失败：API返回非200
        
        # 尝试解析JSON
        try:
            json_data = response.json()
            logger.info("成功解析JSON响应")
            logger.info(f"完整响应: {json.dumps(json_data, indent=2)}")
            return 0  # 成功
        except json.JSONDecodeError:
            logger.error("响应不是有效的JSON格式")
            # 根据用户反馈，非有效JSON时不打印详细响应内容
            return 1  # 业务失败：非JSON响应
            
    except requests.exceptions.RequestException as e:
        logger.error(f"请求异常: {e}") # 打印完整的异常信息
        return 2  # 系统异常：网络错误
    except Exception as e:
        logger.error(f"未预期的错误: {e}") # 打印完整的错误信息
        return 2  # 系统异常：程序错误

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Claude API端点测试启动")
    
    exit_code = test_claude_endpoint()
    
    logger.info("="*50)
    if exit_code == 0:
        logger.info("测试结果: 成功")
    elif exit_code == 1:
        logger.info("测试结果: 业务失败")
    elif exit_code == 2:
        logger.info("测试结果: 系统异常")
    
    logger.info("测试结束")
    
    sys.exit(exit_code)