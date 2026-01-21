"""六爻解读多Agent系统 - 主入口"""
import sys
from loguru import logger

from cli.commands import cli


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="WARNING"
    )

    # 运行CLI
    cli()
