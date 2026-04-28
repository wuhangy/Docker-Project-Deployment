import redis

# 核心配置：在 Ubuntu 本地运行，host 设为 localhost
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # 1. 写入测试数据
    r.set("learning_path", "Mastering Redis")
    r.hset("user:hangyin", mapping={
        "status": "Online",
        "progress": "0 to 1"
    })

    # 2. 读取测试数据
    path = r.get("learning_path")
    status = r.hget("user:hangyin", "status")

    print("✅ 恭喜！Ubuntu 内部 Python 访问 Redis 成功！")
    print(f"读取到的数据: {path}, 用户状态: {status}")

except Exception as e:
    print(f"❌ 还是出错了: {e}")
