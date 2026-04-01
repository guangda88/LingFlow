"""
认证和安全模块
"""
from fastapi import Header, HTTPException, status
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# API Key 验证
VALID_API_KEYS = set()

def load_api_keys():
    """从环境变量加载 API Keys"""
    keys_str = os.getenv("LINGFLOW_API_KEYS", "")
    if not keys_str:
        logger.warning(
            "LINGFLOW_API_KEYS not set - API will reject all requests. "
            "Set LINGFLOW_API_KEYS environment variable with comma-separated keys."
        )
        return

    VALID_API_KEYS.update(key.strip() for key in keys_str.split(","))
    logger.info(f"Loaded {len(VALID_API_KEYS)} API key(s)")

# 启动时加载
load_api_keys()

async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """验证 API Key

    Args:
        x_api_key: 请求头中的 API Key

    Returns:
        API Key 字符串

    Raises:
        HTTPException: API Key 无效
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is required. Use X-API-Key header."
        )

    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    return x_api_key


# 可选的 API Key 验证（不强制）
async def verify_api_key_optional(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """验证 API Key（可选）

    用于不需要认证的端点，但如果有 API Key 则验证
    """
    if not x_api_key:
        return None

    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    return x_api_key
