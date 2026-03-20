"""{{SKILL_NAME}} - {{DESCRIPTION}}"""

import requests

def execute_skill(params):
    """
    执行技能
    
    Args:
        params: 包含以下参数
            - api_key: API密钥（可选）
            - endpoint: API端点
            - payload: 请求数据
    
    Returns:
        dict: API响应结果
    """
    endpoint = params.get('endpoint')
    payload = params.get('payload', {})
    api_key = params.get('api_key')
    
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return {
            'success': True,
            'data': response.json()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
