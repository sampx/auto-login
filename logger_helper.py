import logging
import os

class LoggerHelper:
    @staticmethod
    def get_logger(name=__name__):
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_file = os.getenv('LOG_FILE', 'logs/app.log')        

        # 配置日志记录
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        return logging.getLogger(name)