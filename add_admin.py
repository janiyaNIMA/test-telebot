import asyncio
from database import add_admin, init_db

async def make_me_admin():
    # Ensure database is initialized
    init_db()
    
    admin_id = 5354706112
    print(f"尝试将用户 {admin_id} 设置为管理员...")
    
    success = await add_admin(admin_id)
    if success:
        print(f"✅ 成功！用户 {admin_id} 现在是管理员了。")
    else:
        print(f"ℹ️ 用户 {admin_id} 已经是管理员，无需重复添加。")

if __name__ == "__main__":
    asyncio.run(make_me_admin())
