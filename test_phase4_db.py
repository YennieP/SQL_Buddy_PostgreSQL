# test_phase4_db.py
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sqlbuddy.settings')

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("Testing Phase 4 Database Connection")
print("=" * 70)

print(f"\nDatabase: {os.getenv('DB_NAME')}")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"User: {os.getenv('DB_USER')}")

try:
    import django
    django.setup()
    print("\n✓ Django initialized")
    
    from core.models import User, Student, Problem
    
    print(f"✓ User table: {User.objects.count()} records")
    print(f"✓ Student table: {Student.objects.count()} records")
    print(f"✓ Problem table: {Problem.objects.count()} records")
    
    print("\nSample users:")
    for user in User.objects.all()[:3]:
        print(f"  - {user.name}")
    
    # 检查Phase 4数据
    if User.objects.filter(name__icontains='Pizza').exists():
        print("\n✓✓✓ CONFIRMED: This is Phase 4 database!")
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! All tests passed.")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()