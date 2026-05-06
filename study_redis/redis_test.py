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






import redis

# 1. 建立 Redis 连接
client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)

cursor = 0
all_session_keys = set()  # 使用集合去重

print("开始分批扫描 Session 数据...")

while True:
    # 2. 执行 SCAN 命令
    # cursor: 起始位置
    # match: 匹配模式
    # count: 建议每次扫描的坑位数量（不是返回结果数量）[cite: 1, 3]
    cursor, keys = client.scan(cursor=cursor, match='session:user:*', count=500)
    
    # 3. 收集本次找到的 Key
    if keys:
        all_session_keys.update(keys)
        print(f"当前已找到 {len(all_session_keys)} 个 Key，最新游标为: {cursor}")
    
    # 4. 判断游标是否回到 0，回到 0 则代表扫描结束[cite: 3]
    if cursor == 0:
        break

print(f"扫描圆满结束！总共找到 {len(all_session_keys)} 个用户 Session。")











# 使用python实现读写存储
# 以下是使用 **Python (redis-py)** 实现的 5 种数据类型的读写示例。

## 准备工作

import redis

# 连接 Redis（默认本地 6379，无密码）
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  # 自动将返回结果转为字符串
)


## 1. String – 分布式锁

# 写：加锁（SETNX + EXPIRE 原子操作）
lock_key = "lock:product:1001"
client_id = "client:uuid:abc123"

# SET 命令支持 NX + EX 原子操作
lock_acquired = r.set(lock_key, client_id, nx=True, ex=10)
print(f"加锁成功: {lock_acquired}")

# 读：获取锁持有者
lock_owner = r.get(lock_key)
print(f"锁持有者: {lock_owner}")

# 释放锁（验证持有者后删除）
if lock_owner == client_id:
    r.delete(lock_key)
    print("锁已释放")


## 2. Hash – 存储用户信息

# 写：存储用户信息
user_key = "user:2001"
r.hset(user_key, mapping={
    "name": "张三",
    "age": 28,
    "city": "上海"
})
print("用户信息写入成功")

# 读：获取所有字段
user_data = r.hgetall(user_key)
print(f"用户数据: {user_data}")

# 读：只获取姓名
user_name = r.hget(user_key, "name")
print(f"用户名: {user_name}")


## 3. List – 消息队列

# 写：生产者推送消息
queue_key = "email:queue"
r.lpush(queue_key, "sendEmail:123@qq.com")
r.lpush(queue_key, "sendEmail:456@qq.com")
print("消息已入队")

# 读：消费者取出消息（阻塞式，有消息立即返回）
message = r.rpop(queue_key)
print(f"消费的消息: {message}")

# 读：阻塞式等待消息（超时5秒）
message_blocking = r.brpop(queue_key, timeout=5)
print(f"阻塞获取: {message_blocking}")


## 4. Set – 点赞集合（去重）


# 写：用户点赞
article_key = "art:888:likes"
r.sadd(article_key, "u10086")
r.sadd(article_key, "u10087")
print("点赞记录已添加")

# 读：检查用户是否已点赞
is_liked = r.sismember(article_key, "u10086")
print(f"用户 u10086 是否点赞: {is_liked}")

# 读：获取所有点赞用户
all_likes = r.smembers(article_key)
print(f"点赞用户列表: {all_likes}")

# 读：获取点赞数量
like_count = r.scard(article_key)
print(f"点赞总数: {like_count}")



## 5. ZSet – 游戏排行榜
# 写：添加/更新用户分数
rank_key = "game:rank"
r.zadd(rank_key, {"userA": 1500, "userB": 2000, "userC": 1800})
print("分数已写入排行榜")

# 写：增加用户分数（增量操作）
r.zincrby(rank_key, 100, "userA")  # userA 增加 100 分
print("userA 分数增加100")

# 读：按分数从高到低取前2名（带分数）
top2 = r.zrevrange(rank_key, 0, 1, withscores=True)
print(f"排行榜前2名: {top2}")

# 读：查询 userB 的排名（0 为第一名）
rank = r.zrevrank(rank_key, "userB")
print(f"userB 的排名: {rank + 1}")

# 读：查询 userC 的分数
score = r.zscore(rank_key, "userC")
print(f"userC 的分数: {score}")



## 完整运行示例（可直接复制）

import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.flushdb()  # 清空当前数据库（仅测试用）

# === String ===
r.set("counter", 100)
print(f"String 读取: {r.get('counter')}")

# === Hash ===
r.hset("product:1", mapping={"name": "手机", "price": 2999})
print(f"Hash 读取: {r.hgetall('product:1')}")

# === List ===
r.rpush("queue", "task1", "task2")
print(f"List 读取: {r.lpop('queue')}")

# === Set ===
r.sadd("tags", "redis", "python")
print(f"Set 读取: {r.smembers('tags')}")

# === ZSet ===
r.zadd("score", {"Alice": 95, "Bob": 87})
print(f"ZSet 读取: {r.zrevrange('score', 0, -1, withscores=True)}")


## 安装依赖

# pip install redis


# 如果 Redis 不在本地，可以用连接参数：

r = redis.Redis(
    host='your-redis-host',
    port=6379,
    password='your-password',
    decode_responses=True
)



###ROB 快照
# Python 示例
import redis

r = redis.Redis(decode_responses=True)

# 后台保存
r.bgsave()
print("RDB 后台保存已触发")

# 查看状态
info = r.info('persistence')
print(f"RDB 最后保存时间: {info['rdb_last_save_time']}")
print(f"RDB 是否正在进行: {info['rdb_bgsave_in_progress']}")
################################
# Python 操作 AOF
import redis

r = redis.Redis(decode_responses=True)

# 触发 AOF 重写
r.bgrewriteaof()
print("AOF 重写已触发")

# 查看 AOF 状态
info = r.info('persistence')
print(f"AOF 启用状态: {info['aof_enabled']}")
print(f"AOF 当前大小: {info['aof_current_size']} bytes")
print(f"AOF 重写进度: {info['aof_rewrite_in_progress']}")