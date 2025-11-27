
# ============================================================
# 文件1: core/context_processors.py
# 全局Context - 让所有template都能访问用户信息
# ============================================================

def user_role(request):
    """
    添加用户信息到所有templates
    在templates中可以直接使用 {{ user_id }}, {{ user_name }}, {{ user_role }}
    """
    return {
        'user_id': request.session.get('user_id'),
        'user_name': request.session.get('user_name'),
        'user_email': request.session.get('user_email'),
        'user_role': request.session.get('user_role'),
    }