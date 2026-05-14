from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
import os
import mysql.connector
from mysql.connector import pooling
import hashlib
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# ============ Redis 连接配置 ============
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=6379,
    decode_responses=True,
    db=0
)

# ============ MySQL 连接池配置 ============
db_config = {
    'host': os.getenv('MYSQL_HOST', 'mysql'),
    'user': os.getenv('MYSQL_USER', 'takeout_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'takeout_pass'),
    'database': os.getenv('MYSQL_DATABASE', 'takeout_db'),
    'pool_name': 'mypool',
    'pool_size': 10
}

connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db_connection():
    return connection_pool.get_connection()

# ============ 原有 Redis 订单功能 ============

# 首页
@app.route('/')
def home():
    return jsonify({
        "message": "🍔 外卖系统 API",
        "status": "运行中",
        "version": "2.0",
        "databases": {
            "redis": "用于缓存和会话",
            "mysql": "用于数据持久化"
        },
        "endpoints": {
            "订单管理 (Redis)": {
                "查看所有订单": "/orders",
                "添加订单": "/order (POST)",
                "查询订单": "/order/<id>",
                "删除订单": "/order/<id> (DELETE)",
                "测试Redis": "/test-redis"
            },
            "菜品管理 (MySQL)": {
                "获取所有菜品": "/api/dishes",
                "获取菜品分类": "/api/categories",
                "获取热门菜品": "/api/dishes/popular"
            },
            "用户管理 (MySQL)": {
                "用户登录": "/api/login (POST)",
                "获取订单历史": "/api/orders/history"
            },
            "统计分析 (MySQL)": {
                "仪表板数据": "/api/dashboard/stats",
                "健康检查": "/health"
            }
        }
    })

# 添加订单到 Redis
@app.route('/order', methods=['POST'])
def add_order():
    try:
        data = request.json
        order_id = data.get('id')
        
        if not order_id:
            return jsonify({"error": "需要订单ID"}), 400
        
        # 添加时间戳
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
                "host": os.getenv('REDIS_HOST', 'redis'),
                "port": 6379,
                "ping": redis_client.ping()
            }
        })
    except Exception as e:
        return jsonify({
            "status": "❌ Redis 连接失败",
            "error": str(e)
        }), 500

# 统计信息 (Redis)
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

# ============ 新增 MySQL API 端点 ============

# 获取所有菜品
@app.route('/api/dishes', methods=['GET'])
def get_dishes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        category = request.args.get('category')
        if category:
            cursor.execute("""
                SELECT d.*, c.name as category_name 
                FROM dishes d
                LEFT JOIN categories c ON d.category_id = c.id
                WHERE c.name = %s AND d.status = 'available'
            """, (category,))
        else:
            cursor.execute("""
                SELECT d.*, c.name as category_name 
                FROM dishes d
                LEFT JOIN categories c ON d.category_id = c.id
                WHERE d.status = 'available'
                ORDER BY d.sales_count DESC
            """)
        
        dishes = cursor.fetchall()
        
        # 转换 Decimal 类型
        for dish in dishes:
            if 'price' in dish:
                dish['price'] = float(dish['price'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total": len(dishes),
            "dishes": dishes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取菜品分类
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories ORDER BY sort_order")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "categories": categories
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取菜品详情
@app.route('/api/dishes/<int:dish_id>', methods=['GET'])
def get_dish_detail(dish_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, c.name as category_name 
            FROM dishes d
            LEFT JOIN categories c ON d.category_id = c.id
            WHERE d.id = %s
        """, (dish_id,))
        
        dish = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if dish:
            if 'price' in dish:
                dish['price'] = float(dish['price'])
            return jsonify({
                "success": True,
                "dish": dish
            })
        else:
            return jsonify({"error": "菜品不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "用户名和密码不能为空"}), 400
        
        # 密码加密（与 seed.py 中的加密方式一致）
        hashed_pwd = hashlib.md5(f"{password}".encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, email, phone, address, role FROM users WHERE username = %s AND password = %s",
            (username, hashed_pwd)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            # 存储 session 到 Redis
            session_id = hashlib.md5(f"{username}{datetime.datetime.now()}".encode()).hexdigest()
            redis_client.setex(f"session:{session_id}", 3600, json.dumps(user))
            
            return jsonify({
                "success": True,
                "message": f"欢迎回来，{username}！",
                "user": user,
                "session_id": session_id
            })
        else:
            return jsonify({"error": "用户名或密码错误"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取订单历史（从 MySQL）
@app.route('/api/orders/history', methods=['GET'])
def get_order_history():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "需要用户ID"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT o.*, 
                   GROUP_CONCAT(CONCAT(d.name, ' x', oi.quantity) SEPARATOR ', ') as items,
                   COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN dishes d ON oi.dish_id = d.id
            WHERE o.user_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """, (user_id,))
        
        orders = cursor.fetchall()
        
        # 转换 Decimal 类型
        for order in orders:
            if 'total_amount' in order:
                order['total_amount'] = float(order['total_amount'])
            if 'delivery_fee' in order:
                order['delivery_fee'] = float(order['delivery_fee'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total": len(orders),
            "orders": orders
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取热门菜品
@app.route('/api/dishes/popular', methods=['GET'])
def get_popular_dishes():
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, description, price, sales_count, rating, image_url
            FROM dishes 
            WHERE status = 'available'
            ORDER BY sales_count DESC, rating DESC 
            LIMIT %s
        """, (limit,))
        
        dishes = cursor.fetchall()
        
        for dish in dishes:
            if 'price' in dish:
                dish['price'] = float(dish['price'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "dishes": dishes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取统计仪表板数据
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 今日订单数
        cursor.execute("""
            SELECT COUNT(*) as today_orders 
            FROM orders 
            WHERE DATE(created_at) = CURDATE()
        """)
        today_orders = cursor.fetchone()['today_orders']
        
        # 今日销售额
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as today_sales 
            FROM orders 
            WHERE DATE(created_at) = CURDATE() AND status = 'completed'
        """)
        today_sales = cursor.fetchone()['today_sales']
        
        # 今日订单数（按状态分组）
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM orders 
            WHERE DATE(created_at) = CURDATE()
            GROUP BY status
        """)
        today_orders_by_status = cursor.fetchall()
        
        # 总用户数
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()['total_users']
        
        # 总菜品数
        cursor.execute("SELECT COUNT(*) as total_dishes FROM dishes WHERE status = 'available'")
        total_dishes = cursor.fetchone()['total_dishes']
        
        # 总订单数
        cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
        total_orders = cursor.fetchone()['total_orders']
        
        # 总收入
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status = 'completed'")
        total_revenue = cursor.fetchone()['total_revenue']
        
        # 热门菜品 Top 5
        cursor.execute("""
            SELECT name, sales_count, rating 
            FROM dishes 
            ORDER BY sales_count DESC 
            LIMIT 5
        """)
        popular_dishes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "today": {
                    "orders": today_orders,
                    "sales": float(today_sales),
                    "by_status": today_orders_by_status
                },
                "total": {
                    "users": total_users,
                    "dishes": total_dishes,
                    "orders": total_orders,
                    "revenue": float(total_revenue)
                },
                "popular_dishes": popular_dishes
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取所有用户（管理员功能）
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, email, phone, address, role, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total": len(users),
            "users": users
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取订单详情（包含明细）
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取订单信息
        cursor.execute("""
            SELECT o.*, u.username, u.phone
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            return jsonify({"error": "订单不存在"}), 404
        
        # 获取订单明细
        cursor.execute("""
            SELECT oi.*, d.name, d.image_url
            FROM order_items oi
            LEFT JOIN dishes d ON oi.dish_id = d.id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        items = cursor.fetchall()
        
        # 转换 Decimal
        if 'total_amount' in order:
            order['total_amount'] = float(order['total_amount'])
        if 'delivery_fee' in order:
            order['delivery_fee'] = float(order['delivery_fee'])
        
        for item in items:
            if 'price' in item:
                item['price'] = float(item['price'])
            if 'subtotal' in item:
                item['subtotal'] = float(item['subtotal'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "order": order,
            "items": items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 搜索菜品
@app.route('/api/dishes/search', methods=['GET'])
def search_dishes():
    try:
        keyword = request.args.get('q', '')
        if not keyword:
            return jsonify({"error": "请输入搜索关键词"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, description, price, sales_count, rating
            FROM dishes 
            WHERE status = 'available' 
            AND (name LIKE %s OR description LIKE %s)
            ORDER BY sales_count DESC
            LIMIT 20
        """, (f'%{keyword}%', f'%{keyword}%'))
        
        dishes = cursor.fetchall()
        
        for dish in dishes:
            if 'price' in dish:
                dish['price'] = float(dish['price'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total": len(dishes),
            "dishes": dishes,
            "keyword": keyword
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    checks = {
        "redis": False,
        "mysql": False,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # 检查 Redis
    try:
        redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        checks["redis_error"] = str(e)
    
    # 检查 MySQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        checks["mysql"] = True
    except Exception as e:
        checks["mysql_error"] = str(e)
    
    status = "healthy" if all([checks["redis"], checks["mysql"]]) else "unhealthy"
    
    return jsonify({
        "status": status,
        "checks": checks
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')
        address = data.get('address', '')
        
        # 验证必填字段
        if not username or not password or not email:
            return jsonify({"error": "用户名、密码和邮箱为必填项"}), 400
        
        # 检查用户名是否已存在
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "用户名已存在"}), 400
        
        # 检查邮箱是否已存在
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "邮箱已被注册"}), 400
        
        # 加密密码
        hashed_pwd = hashlib.md5(password.encode()).hexdigest()
        
        # 插入新用户
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, address, role) 
            VALUES (%s, %s, %s, %s, %s, 'customer')
        """, (username, hashed_pwd, email, phone, address))
        conn.commit()
        
        # 获取新用户信息
        user_id = cursor.lastrowid
        cursor.execute("SELECT id, username, email, phone, address, role FROM users WHERE id = %s", (user_id,))
        new_user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 自动登录（返回 session）
        import datetime
        session_id = hashlib.md5(f"{username}{datetime.datetime.now()}".encode()).hexdigest()
        redis_client.setex(f"session:{session_id}", 3600, json.dumps(new_user))
        
        return jsonify({
            "success": True,
            "message": "注册成功！",
            "user": new_user,
            "session_id": session_id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

