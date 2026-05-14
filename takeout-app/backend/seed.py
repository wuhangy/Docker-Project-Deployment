import mysql.connector
from datetime import datetime, timedelta
import random
import hashlib

# 数据库连接配置
db_config = {
    'host': 'mysql',
    'user': 'takeout_user',
    'password': 'takeout_pass',
    'database': 'takeout_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def generate_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🌱 开始生成示例数据...")
    
    # 1. 插入菜品分类
    categories = [
        ('🍔 汉堡套餐', 'burger', 1),
        ('🍕 披萨', 'pizza', 2),
        ('🍜 中式快餐', 'chinese', 3),
        ('🍣 寿司', 'sushi', 4),
        ('🥗 沙拉轻食', 'salad', 5),
        ('🥤 饮品', 'drink', 6),
        ('🍰 甜品', 'dessert', 7)
    ]
    
    for cat in categories:
        cursor.execute(
            "INSERT INTO categories (name, icon, sort_order) VALUES (%s, %s, %s)",
            cat
        )
    print(f"✅ 添加了 {len(categories)} 个菜品分类")
    
    # 获取分类ID映射
    cursor.execute("SELECT id, name FROM categories")
    cat_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # 2. 插入菜品
    dishes = [
        # 汉堡类
        ('经典牛肉汉堡', '100%纯牛肉，搭配新鲜生菜和番茄', 28.00, cat_map['🍔 汉堡套餐'], 150, 4.6),
        ('双层芝士汉堡', '双层牛肉饼，双层芝士，口感丰富', 42.00, cat_map['🍔 汉堡套餐'], 98, 4.8),
        ('香辣鸡腿堡', '香辣多汁的鸡腿肉', 26.00, cat_map['🍔 汉堡套餐'], 210, 4.5),
        
        # 披萨类
        ('超级至尊披萨', '培根、火腿、牛肉、青椒、洋葱', 68.00, cat_map['🍕 披萨'], 88, 4.7),
        ('海鲜披萨', '虾仁、鱿鱼、蟹柳', 78.00, cat_map['🍕 披萨'], 45, 4.9),
        ('夏威夷披萨', '火腿、菠萝', 58.00, cat_map['🍕 披萨'], 120, 4.4),
        
        # 中式快餐
        ('宫保鸡丁饭', '经典川菜，鸡肉嫩滑', 32.00, cat_map['🍜 中式快餐'], 300, 4.5),
        ('红烧肉饭', '肥而不腻，入口即化', 38.00, cat_map['🍜 中式快餐'], 180, 4.7),
        ('鱼香肉丝饭', '酸甜微辣', 30.00, cat_map['🍜 中式快餐'], 250, 4.3),
        
        # 寿司
        ('三文鱼寿司拼盘', '新鲜三文鱼6片', 58.00, cat_map['🍣 寿司'], 65, 4.8),
        ('加州卷', '牛油果、蟹柳、黄瓜', 45.00, cat_map['🍣 寿司'], 120, 4.6),
        
        # 沙拉
        ('凯撒沙拉', '罗马生菜、面包丁、帕玛森奶酪', 32.00, cat_map['🥗 沙拉轻食'], 95, 4.5),
        ('水果沙拉', '时令鲜果', 28.00, cat_map['🥗 沙拉轻食'], 88, 4.4),
        
        # 饮品
        ('珍珠奶茶', 'Q弹珍珠', 15.00, cat_map['🥤 饮品'], 500, 4.6),
        ('鲜榨橙汁', '100%鲜橙', 18.00, cat_map['🥤 饮品'], 320, 4.7),
        ('美式咖啡', '现磨咖啡豆', 22.00, cat_map['🥤 饮品'], 200, 4.5),
        
        # 甜品
        ('提拉米苏', '意大利经典甜品', 28.00, cat_map['🍰 甜品'], 150, 4.8),
        ('巧克力熔岩蛋糕', '流心巧克力', 32.00, cat_map['🍰 甜品'], 98, 4.9),
        ('草莓冰淇淋', '新鲜草莓搭配香草冰淇淋', 18.00, cat_map['🍰 甜品'], 280, 4.7),
    ]
    
    for dish in dishes:
        cursor.execute("""
            INSERT INTO dishes (name, description, price, category_id, sales_count, rating)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, dish)
    print(f"✅ 添加了 {len(dishes)} 个菜品")
    
    # 3. 插入用户
    users = [
        ('张三', 'zhangsan@example.com', '13800138001', '北京市朝阳区xxx路1号'),
        ('李四', 'lisi@example.com', '13800138002', '上海市浦东新区xxx路2号'),
        ('王五', 'wangwu@example.com', '13800138003', '广州市天河区xxx路3号'),
        ('赵六', 'zhaoliu@example.com', '13800138004', '深圳市南山区xxx路4号'),
        ('小红', 'xiaohong@example.com', '13800138005', '杭州市西湖区xxx路5号'),
    ]
    
    user_ids = []
    for user in users:
        # 简单密码加密（实际项目应使用 bcrypt）
        hashed_pwd = hashlib.md5(f"{user[0]}123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, address)
            VALUES (%s, %s, %s, %s, %s)
        """, (user[0], hashed_pwd, user[1], user[2], user[3]))
        user_ids.append(cursor.lastrowid)
    print(f"✅ 添加了 {len(users)} 个用户")
    
    # 4. 插入订单和订单明细
    statuses = ['pending', 'paid', 'preparing', 'delivering', 'completed', 'cancelled']
    payment_methods = ['cash', 'wechat', 'alipay', 'card']
    
    # 获取菜品ID列表和价格
    cursor.execute("SELECT id, price FROM dishes")
    dish_info = cursor.fetchall()
    dish_prices = {d[0]: float(d[1]) for d in dish_info}
    dish_ids = list(dish_prices.keys())
    
    order_nos = []
    
    for i in range(30):  # 生成30个订单
        user_id = random.choice(user_ids)
        status = random.choice(statuses)
        payment_method = random.choice(payment_methods)
        
        # 随机订单时间（最近30天内）
        days_ago = random.randint(0, 30)
        order_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # 随机生成2-5个菜品
        num_items = random.randint(2, 5)
        selected_dishes = random.sample(dish_ids, min(num_items, len(dish_ids)))
        
        total_amount = 0
        items = []
        
        for dish_id in selected_dishes:
            quantity = random.randint(1, 3)
            price = dish_prices[dish_id]
            subtotal = price * quantity
            total_amount += subtotal
            items.append((dish_id, quantity, price, subtotal))
        
        # 添加配送费
        delivery_fee = 5.0
        total_amount += delivery_fee
        
        # 生成订单号
        order_no = f"ORD{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}"
        order_nos.append(order_no)
        
        cursor.execute("""
            INSERT INTO orders (order_no, user_id, total_amount, status, payment_method, 
                              delivery_address, delivery_fee, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (order_no, user_id, total_amount, status, payment_method, 
              f"地址{user_id}", delivery_fee, order_time))
        
        order_id = cursor.lastrowid
        
        # 插入订单明细
        for dish_id, quantity, price, subtotal in items:
            cursor.execute("""
                INSERT INTO order_items (order_id, dish_id, quantity, price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, dish_id, quantity, price, subtotal))
        
        # 如果订单已完成，更新菜品销量
        if status == 'completed':
            for dish_id, quantity, _, _ in items:
                cursor.execute("""
                    UPDATE dishes SET sales_count = sales_count + %s 
                    WHERE id = %s
                """, (quantity, dish_id))
    
    print(f"✅ 添加了 30 个订单")
    
    # 5. 添加评价（为部分已完成订单添加评价）
    cursor.execute("SELECT id, order_id, user_id FROM orders WHERE status = 'completed' LIMIT 15")
    completed_orders = cursor.fetchall()
    
    comments = [
        '非常好吃，下次还来！', '味道不错，配送很快', '包装很精美', 
        '量很足，很满意', '有点辣，但是很好吃', '配送小哥态度很好',
        '价格实惠，性价比高', '食物新鲜，推荐！', '味道一般，有待改进',
        '超赞！五星好评', '不错不错，很满意'
    ]
    
    for order in completed_orders[:15]:
        order_id, order_table_id, user_id = order
        
        # 获取该订单的菜品
        cursor.execute("SELECT dish_id FROM order_items WHERE order_id = %s", (order_table_id,))
        order_dishes = cursor.fetchall()
        
        for dish in order_dishes[:2]:  # 每个订单最多2个评价
            rating = random.randint(3, 5)
            comment = random.choice(comments)
            cursor.execute("""
                INSERT INTO reviews (order_id, user_id, dish_id, rating, comment)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_table_id, user_id, dish[0], rating, comment))
    
    print(f"✅ 添加了 15+ 条用户评价")
    
    # 6. 添加优惠券
    coupons = [
        ('NEW2024', '新人专享券', 'fixed', 10.00, 20.00, '2024-01-01', '2024-12-31', 1),
        ('VIP88', 'VIP专属券', 'percentage', 15.00, 50.00, '2024-01-01', '2024-12-31', 5),
        ('SPRING', '春季大促', 'fixed', 20.00, 80.00, '2024-03-01', '2024-05-31', 3),
        ('FREESHIP', '免配送费', 'fixed', 5.00, 30.00, '2024-01-01', '2024-12-31', 10),
    ]
    
    for coupon in coupons:
        cursor.execute("""
            INSERT INTO coupons (code, description, discount_type, discount_value, 
                               min_amount, start_date, end_date, usage_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, coupon)
    
    print(f"✅ 添加了 {len(coupons)} 张优惠券")
    
    # 提交事务
    conn.commit()
    
    # 输出统计信息
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dishes")
    dish_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reviews")
    review_count = cursor.fetchone()[0]
    
    print("\n" + "="*50)
    print("📊 数据库统计：")
    print(f"   用户数：{user_count}")
    print(f"   菜品数：{dish_count}")
    print(f"   订单数：{order_count}")
    print(f"   评价数：{review_count}")
    print("="*50)
    
    cursor.close()
    conn.close()
    print("\n🎉 示例数据生成完成！")

if __name__ == "__main__":
    generate_sample_data()


