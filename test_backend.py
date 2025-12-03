"""
SQL Buddy 后端功能测试脚本
逐步验证每个组件是否正常工作
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sqlbuddy.settings')
django.setup()

from core.models import *
from django.contrib.auth.models import User
from django.db import connection

def test_database_connection():
    """测试1: 数据库连接"""
    print("\n" + "="*60)
    print("测试1: 数据库连接")
    print("="*60)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print(f"✅ 成功连接到数据库: {db_name}")
            
            # 检查表
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"✅ 发现 {len(tables)} 个表")
            
            # 列出前10个表
            print("\n前10个表:")
            for i, table in enumerate(tables[:10], 1):
                print(f"   {i}. {table}")
            
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_models_import():
    """测试2: Models导入"""
    print("\n" + "="*60)
    print("测试2: Models导入检查")
    print("="*60)
    
    models_to_check = [
        'User', 'Student', 'Mentor', 'Admin',
        'Topic', 'Problem', 'TestCase', 'Attempt',
        'Scenario', 'Resource', 'Notification'
    ]
    
    success_count = 0
    for model_name in models_to_check:
        try:
            model = globals().get(model_name)
            if model and hasattr(model, 'objects'):
                count = model.objects.count()
                print(f"   ✅ {model_name}: {count} 条记录")
                success_count += 1
            else:
                print(f"   ⚠️  {model_name}: Model未定义")
        except Exception as e:
            print(f"   ❌ {model_name}: {e}")
    
    print(f"\n总结: {success_count}/{len(models_to_check)} 个Models可用")
    return success_count == len(models_to_check)

def test_student_views_imports():
    """测试3: Student Views导入"""
    print("\n" + "="*60)
    print("测试3: Student Views导入检查")
    print("="*60)
    
    try:
        from core.views import student_views
        
        # 检查view函数
        view_functions = [
            'student_dashboard',
            'browse_problems', 
            'problem_detail',
            'submit_attempt',
            'my_attempts',
            'nl_query',
        ]
        
        found_functions = []
        for func_name in view_functions:
            if hasattr(student_views, func_name):
                found_functions.append(func_name)
                print(f"   ✅ {func_name}")
            else:
                print(f"   ❌ {func_name} - 未找到")
        
        print(f"\n总结: {len(found_functions)}/{len(view_functions)} 个Student views可用")
        return len(found_functions) > 0
        
    except ImportError as e:
        print(f"❌ 无法导入student_views: {e}")
        return False

def test_mentor_views_imports():
    """测试4: Mentor Views导入"""
    print("\n" + "="*60)
    print("测试4: Mentor Views导入检查")
    print("="*60)
    
    try:
        from core.views import mentor_views
        
        # 检查view函数
        view_functions = [
            'mentor_dashboard',
            'create_problem',
            'my_problems',
            'review_attempts',
            'mentor_nl_query',
        ]
        
        found_functions = []
        for func_name in view_functions:
            if hasattr(mentor_views, func_name):
                found_functions.append(func_name)
                print(f"   ✅ {func_name}")
            else:
                print(f"   ❌ {func_name} - 未找到")
        
        print(f"\n总结: {len(found_functions)}/{len(view_functions)} 个Mentor views可用")
        return len(found_functions) > 0
        
    except ImportError as e:
        print(f"❌ 无法导入mentor_views: {e}")
        return False

def test_utils_modules():
    """测试5: Utils模块"""
    print("\n" + "="*60)
    print("测试5: Utils模块导入检查")
    print("="*60)
    
    utils_modules = {
        'nl2sql': ['convert_nl_to_sql'],
        'scenario_generator': ['generate_scenario_problems'],
        'sql_evaluator': ['evaluate_sql'],
    }
    
    success_count = 0
    for module_name, functions in utils_modules.items():
        try:
            module = __import__(f'core.utils.{module_name}', fromlist=functions)
            
            found_funcs = []
            for func_name in functions:
                if hasattr(module, func_name):
                    found_funcs.append(func_name)
            
            if found_funcs:
                print(f"   ✅ {module_name}: {', '.join(found_funcs)}")
                success_count += 1
            else:
                print(f"   ⚠️  {module_name}: 已导入但未找到预期函数")
                
        except ImportError as e:
            print(f"   ❌ {module_name}: 无法导入 - {e}")
    
    print(f"\n总结: {success_count}/{len(utils_modules)} 个Utils模块可用")
    return success_count > 0

def test_urls_configuration():
    """测试6: URLs配置"""
    print("\n" + "="*60)
    print("测试6: URLs配置检查")
    print("="*60)
    
    try:
        from django.urls import get_resolver
        from django.urls.exceptions import NoReverseMatch
        
        resolver = get_resolver()
        url_patterns = resolver.url_patterns
        
        print(f"   ✅ 发现 {len(url_patterns)} 个URL模式")
        
        # 尝试reverse一些关键URLs
        test_urls = [
            'login',
            'student_dashboard',
            'mentor_dashboard',
            'browse_problems',
        ]
        
        from django.urls import reverse
        found_urls = []
        
        for url_name in test_urls:
            try:
                path = reverse(url_name)
                found_urls.append(url_name)
                print(f"   ✅ {url_name} -> {path}")
            except NoReverseMatch:
                print(f"   ❌ {url_name} - 未配置")
        
        print(f"\n总结: {len(found_urls)}/{len(test_urls)} 个关键URL已配置")
        return len(found_urls) > 0
        
    except Exception as e:
        print(f"❌ URLs配置检查失败: {e}")
        return False

def test_templates_exist():
    """测试7: Templates文件存在性"""
    print("\n" + "="*60)
    print("测试7: Templates文件检查")
    print("="*60)
    
    from pathlib import Path
    templates_dir = Path('core/templates/core')
    
    if not templates_dir.exists():
        print(f"❌ Templates目录不存在: {templates_dir}")
        return False
    
    templates = list(templates_dir.glob('*.html'))
    print(f"   ✅ 发现 {len(templates)} 个模板文件")
    
    # 列出前10个
    print("\n前10个模板:")
    for i, template in enumerate(templates[:10], 1):
        print(f"   {i}. {template.name}")
    
    return len(templates) > 0

def test_static_files():
    """测试8: Static文件"""
    print("\n" + "="*60)
    print("测试8: Static文件检查")
    print("="*60)
    
    from pathlib import Path
    static_dir = Path('core/static')
    
    if not static_dir.exists():
        print(f"❌ Static目录不存在: {static_dir}")
        return False
    
    css_files = list((static_dir / 'css').glob('*.css')) if (static_dir / 'css').exists() else []
    js_files = list((static_dir / 'js').glob('*.js')) if (static_dir / 'js').exists() else []
    
    print(f"   ✅ CSS文件: {len(css_files)} 个")
    print(f"   ✅ JS文件: {len(js_files)} 个")
    
    return True

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print(" SQL Buddy 后端功能测试")
    print("="*60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("Models导入", test_models_import),
        ("Student Views", test_student_views_imports),
        ("Mentor Views", test_mentor_views_imports),
        ("Utils模块", test_utils_modules),
        ("URLs配置", test_urls_configuration),
        ("Templates文件", test_templates_exist),
        ("Static文件", test_static_files),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试失败: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*60)
    print(" 测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} - {test_name}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！后端基础功能正常！")
    elif passed > total // 2:
        print("\n⚠️  部分测试失败，但核心功能可用")
    else:
        print("\n❌ 多个测试失败，需要修复后才能继续")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()