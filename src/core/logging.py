"""
日志配置模块
"""

import logging
import sys
from typing import Optional

from .config import get_settings


def setup_logging(
    level: Optional[str] = None, format_string: Optional[str] = None
) -> logging.Logger:
    """
    配置日志系统

    Args:
        level: 日志级别
        format_string: 日志格式

    Returns:
        配置好的 logger 实例
    """
    settings = get_settings()
    log_level = level or ("DEBUG" if settings.debug else "INFO")
    log_format = format_string or (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )

    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # 创建应用日志器
    logger = logging.getLogger(settings.project_name)
    logger.setLevel(getattr(logging, log_level))

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger"""
    settings = get_settings()
    return logging.getLogger(f"{settings.project_name}.{name}")
