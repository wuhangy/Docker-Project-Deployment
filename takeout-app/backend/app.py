from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
import os

app = Flask(__name__)
CORS(app)

# 连接到 Redis 数据库
# 'db' 是 docker-compose.yml 中定义的服务名
redis_client = redis.Redis(
    host='db',      # Redis 服务名
    port=6379,
    decode_responses=True,
    db=0
)

# 首页
@app.route('/')
def home():
    return jsonify({
        "message": "🍔 外卖系统 API",
        "status": "运行中",
        "endpoints": {
            "查看所有订单": "/orders",
            "添加订单": "/order (POST)",
            "查询订单": "/order/<id>",
            "测试Redis": "/test-redis"
        }
    })

# 添加订单
@app.route('/order', methods=['POST'])
def add_order():
    try:
        data = request.json
        order_id = data.get('id')
        
        if not order_id:
            return jsonify({"error": "需要订单ID"}), 400
        
        # 添加时间戳
        import datetime
        data['created_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存到 Redis
        redis_client.set(f'order:{order_id}', json.dumps(data))
        
        return jsonify({
            "success": True,
            "message": f"订单 {order_id} 已添加",
            "order": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 查询单个订单
@app.route('/order/<order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = redis_client.get(f'order:{order_id}')
        
        if order:
            return jsonify(json.loads(order))
        else:
            return jsonify({"error": f"订单 {order_id} 不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 查看所有订单
@app.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        # 查找所有订单键
        keys = redis_client.keys('order:*')
        orders = []
        
        for key in keys:
            order_data = redis_client.get(key)
            if order_data:
                order = json.loads(order_data)
                order['key'] = key
                orders.append(order)
        
        return jsonify({
            "total": len(orders),
            "orders": orders
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 删除订单
@app.route('/order/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        result = redis_client.delete(f'order:{order_id}')
        
        if result:
            return jsonify({"success": True, "message": f"订单 {order_id} 已删除"})
        else:
            return jsonify({"error": f"订单 {order_id} 不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 测试 Redis 连接
@app.route('/test-redis', methods=['GET'])
def test_redis():
    try:
        # 测试写入
        redis_client.set('test_key', 'test_value')
        # 测试读取
        value = redis_client.get('test_key')
        # 测试删除
        redis_client.delete('test_key')
        
        return jsonify({
            "status": "✅ Redis 连接成功！",
            "test_result": value,
            "redis_info": {
                "host": "db",
                "port": 6379,
                "ping": redis_client.ping()
            }
        })
    except Exception as e:
        return jsonify({
            "status": "❌ Redis 连接失败",
            "error": str(e)
        }), 500

# 统计信息
@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        keys = redis_client.keys('order:*')
        return jsonify({
            "total_orders": len(keys),
            "redis_status": "connected",
            "database_size": redis_client.dbsize()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)