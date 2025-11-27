# test_simple.py
print("Starting test...")

# 1. 测试环境变量
from dotenv import load_dotenv
import os

load_dotenv()
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")

# 2. 测试PyMySQL连接
try:
    import pymysql

    print("PyMySQL imported successfully")

    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
    )

    print("✓ Database connection successful!")

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM User")
    count = cursor.fetchone()[0]
    print(f"✓ User table has {count} records")

    cursor.execute("SELECT name FROM User LIMIT 3")
    users = cursor.fetchall()
    print("✓ Sample users:")
    for user in users:
        print(f"  - {user[0]}")

    cursor.close()
    conn.close()
    print("\n✅ SUCCESS!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback

    traceback.print_exc()
