import sys
import os
from loguru import logger

def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logger.remove()
    logger.add(
        sys.stdout, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", 
        level="INFO"
    )
    logger.add(
        f"{log_dir}/system.log", 
        rotation="10 MB", 
        retention="30 days", 
        compression="zip",
        level="DEBUG"
    )
    return logger

sys_logger = setup_logger()