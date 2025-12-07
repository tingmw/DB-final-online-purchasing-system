# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
from datetime import datetime
import sys
import os

# 確保可以從父目錄導入 shopping_db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shopping_db import OnlineShoppingDB

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'


DATABASE = 'online_shopping.db'


def get_db():
    if 'db' not in g:
        g.db = OnlineShoppingDB(db_name=DATABASE)
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db_instance = g.pop('db', None)
    if db_instance is not None:
        db_instance.close()

@app.route('/search', methods=['GET'])
def search():
    db_instance = get_db()
    query_type = request.args.get('query_type')
    search_term = request.args.get('search_term', '').strip()
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    customer_id = request.args.get('customer_id')

    products = []
    customers = []
    orders = []
    # 這裡我們只處理查詢結果，其他表格保持原樣或為空
    suppliers = db_instance.fetch_all("Suppliers") # 為了保持頁面完整性
    order_items = db_instance.fetch_all("Order_Items")
    product_suppliers = db_instance.fetch_all("Product_Suppliers")

    try:
        if query_type == 'product_by_name':
            if search_term:
                # 模糊查詢商品名稱
                products = db_instance.cursor.execute(
                    "SELECT * FROM Products WHERE name LIKE ?", ('%' + search_term + '%',)
                ).fetchall()
                flash(f"查詢商品名稱包含 '{search_term}' 的結果。", 'info')
            else:
                flash("請輸入商品名稱進行查詢。", 'warning')

        elif query_type == 'products_in_price_range':
            if min_price and max_price:
                min_price = float(min_price)
                max_price = float(max_price)
                products = db_instance.cursor.execute(
                    "SELECT * FROM Products WHERE price BETWEEN ? AND ?", (min_price, max_price)
                ).fetchall()
                flash(f"查詢價格介於 {min_price} 到 {max_price} 的商品。", 'info')
            else:
                flash("請輸入有效的價格範圍。", 'warning')

        elif query_type == 'customer_by_email':
            if search_term:
                # 精確查詢顧客 Email
                customers = db_instance.fetch_all("Customers", {"email": search_term})
                flash(f"查詢 Email 為 '{search_term}' 的顧客結果。", 'info')
            else:
                flash("請輸入顧客 Email 進行查詢。", 'warning')

        elif query_type == 'orders_by_customer':
            if customer_id:
                customer_id = int(customer_id)
                orders = db_instance.fetch_all("Orders", {"customer_id": customer_id})
                flash(f"查詢顧客 ID {customer_id} 的所有訂單。", 'info')
            else:
                flash("請選擇顧客 ID 進行查詢。", 'warning')

        elif query_type == 'products_low_stock':
            # 查詢庫存量低於特定值的商品 (假設為 10)
            products = db_instance.cursor.execute(
                "SELECT * FROM Products WHERE stock_quantity < ?", (10,)
            ).fetchall()
            flash("查詢庫存量少於 10 的商品。", 'info')
        else:
            flash("請選擇一個查詢類型。", 'warning')

    except ValueError:
        flash("輸入格式不正確，請檢查。", 'danger')
    except Exception as e:
        flash(f"查詢失敗：{e}", 'danger')

    return render_template(
        'index.html',
        products=products,
        customers=customers,
        suppliers=suppliers,
        orders=orders,
        order_items=order_items,
        product_suppliers=product_suppliers,
        # 將查詢參數傳回模板以保持表單狀態
        query_type=query_type,
        search_term=search_term,
        min_price=min_price,
        max_price=max_price,
        customer_id=customer_id
    )

# --- 現有路由 (不變動) ---
@app.route('/')
def index():
    # 初始顯示所有資料，不帶查詢條件
    db_instance = get_db()
    products = db_instance.fetch_all("Products")
    customers = db_instance.fetch_all("Customers")
    suppliers = db_instance.fetch_all("Suppliers")
    orders = db_instance.fetch_all("Orders")
    order_items = db_instance.fetch_all("Order_Items")
    product_suppliers = db_instance.fetch_all("Product_Suppliers")

    return render_template(
        'index.html',
        products=products,
        customers=customers,
        suppliers=suppliers,
        orders=orders,
        order_items=order_items,
        product_suppliers=product_suppliers
    )


# --- 商品 (Products) 操作 ---
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    db_instance = get_db()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        category = request.form['category']

        data = {
            "name": name,
            "description": description,
            "price": price,
            "stock_quantity": stock_quantity,
            "category": category
        }
        product_id = db_instance.insert_data("Products", data)
        if product_id:
            flash(f"商品 '{name}' (ID: {product_id}) 新增成功！", 'success')
        else:
            flash("新增商品失敗！", 'danger')
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    db_instance = get_db()
    product = db_instance.fetch_one("Products", {"product_id": product_id})
    if not product:
        flash("商品不存在！", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        category = request.form['category']

        data = {
            "name": name,
            "description": description,
            "price": price,
            "stock_quantity": stock_quantity,
            "category": category
        }
        updated_rows = db_instance.update_data("Products", data, {"product_id": product_id})
        if updated_rows:
            flash(f"商品 ID {product_id} 更新成功！", 'success')
        else:
            flash("更新商品失敗！", 'danger')
        return redirect(url_for('index'))
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:product_id>')
def delete_product(product_id):
    db_instance = get_db()
    deleted_rows = db_instance.delete_data("Products", {"product_id": product_id})
    if deleted_rows:
        flash(f"商品 ID {product_id} 刪除成功！", 'success')
    else:
        flash("刪除商品失敗！", 'danger')
    return redirect(url_for('index'))

# --- 顧客 (Customers) 操作 ---
@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    db_instance = get_db()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']

        data = {
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "address": address
        }
        customer_id = db_instance.insert_data("Customers", data)
        if customer_id:
            flash(f"顧客 '{name}' (ID: {customer_id}) 新增成功！", 'success')
        else:
            flash("新增顧客失敗！請檢查 Email 是否重複。", 'danger')
        return redirect(url_for('index'))
    return render_template('add_customer.html')

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    db_instance = get_db()
    customer = db_instance.fetch_one("Customers", {"customer_id": customer_id})
    if not customer:
        flash("顧客不存在！", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']

        data = {
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "address": address
        }
        updated_rows = db_instance.update_data("Customers", data, {"customer_id": customer_id})
        if updated_rows:
            flash(f"顧客 ID {customer_id} 更新成功！", 'success')
        else:
            flash("更新顧客失敗！", 'danger')
        return redirect(url_for('index'))
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:customer_id>')
def delete_customer(customer_id):
    db_instance = get_db()
    deleted_rows = db_instance.delete_data("Customers", {"customer_id": customer_id})
    if deleted_rows:
        flash(f"顧客 ID {customer_id} 刪除成功！", 'success')
    else:
        flash("刪除顧客失敗！", 'danger')
    return redirect(url_for('index'))


# --- 訂單 (Orders) 操作 - 包含事務處理 ---
@app.route('/orders/new', methods=['GET', 'POST'])
def new_order():
    db_instance = get_db()
    customers = db_instance.fetch_all("Customers")
    products = db_instance.fetch_all("Products")

    if request.method == 'POST':
        customer_id = int(request.form['customer_id'])
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        product_details = []
        for i in range(len(product_ids)):
            try:
                product_id = int(product_ids[i])
                quantity = int(quantities[i])
                if quantity <= 0:
                    raise ValueError("購買數量必須大於 0。")
                product_details.append({'product_id': product_id, 'quantity': quantity})
            except ValueError:
                flash(f"商品數量或ID格式不正確。", 'danger')
                return redirect(url_for('new_order'))

        if not product_details:
            flash("請至少選擇一個商品。", 'danger')
            return redirect(url_for('new_order'))

        order_id = db_instance.add_order_and_items_transaction(customer_id, product_details)

        if order_id:
            flash(f"新訂單 (ID: {order_id}) 成功建立！", 'success')
        else:
            flash("建立訂單失敗，請檢查庫存或輸入。", 'danger')
        return redirect(url_for('index'))

    return render_template('new_order.html', customers=customers, products=products)


# --- 應用程式啟動時的初始化資料 ---
with app.app_context():
    initial_db_instance = get_db()
    if not initial_db_instance.fetch_all("Products"):
        print("首次運行：插入初始範例資料...")
        product1_id = initial_db_instance.insert_data("Products", {
            "name": "無線藍牙耳機", "description": "高音質、舒適配戴",
            "price": 999.0, "stock_quantity": 50, "category": "電子產品"
        })
        product2_id = initial_db_instance.insert_data("Products", {
            "name": "機械式鍵盤", "description": "青軸，手感極佳",
            "price": 1200.0, "stock_quantity": 30, "category": "電腦週邊"
        })
        product3_id = initial_db_instance.insert_data("Products", {
            "name": "人體工學滑鼠", "description": "緩解手腕疲勞",
            "price": 450.0, "stock_quantity": 100, "category": "電腦週邊"
        })

        supplier1_id = initial_db_instance.insert_data("Suppliers", {
            "name": "XYZ 電子", "contact_email": "info@xyz.com",
            "phone": "02-12345678", "address": "台北市科技大道1號"
        })
        supplier2_id = initial_db_instance.insert_data("Suppliers", {
            "name": "ABC 周邊", "contact_email": "support@abc.com",
            "phone": "03-87654321", "address": "新北市創新園區2號"
        })

        if product1_id and supplier1_id:
            initial_db_instance.insert_data("Product_Suppliers", {"product_id": product1_id, "supplier_id": supplier1_id, "supply_price": 750.0})
        if product2_id and supplier2_id:
            initial_db_instance.insert_data("Product_Suppliers", {"product_id": product2_id, "supplier_id": supplier2_id, "supply_price": 900.0})
        if product3_id and supplier2_id:
            initial_db_instance.insert_data("Product_Suppliers", {"product_id": product3_id, "supplier_id": supplier2_id, "supply_price": 300.0})

        customer1_id = initial_db_instance.insert_data("Customers", {
            "name": "王小明", "email": "xiaoming@example.com",
            "password": "hashed_password_1", "phone": "0912-345678", "address": "台中市西區民生路"
        })
        customer2_id = initial_db_instance.insert_data("Customers", {
            "name": "陳美麗", "email": "meili@example.com",
            "password": "hashed_password_2", "phone": "0987-654321", "address": "高雄市左營區勝利路"
        })
        print("初始資料插入完成。")

if __name__ == '__main__':
    app.run(debug=True)