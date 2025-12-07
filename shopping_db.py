import sqlite3
from datetime import datetime

class OnlineShoppingDB:
    def __init__(self, db_name="online_shopping.db"):
        """
        初始化資料庫連接，並建立資料表（如果不存在）。
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """建立資料庫連接。"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"成功連接到資料庫：{self.db_name}")
        except sqlite3.Error as e:
            print(f"資料庫連接失敗：{e}")

    def _create_tables(self):
        """建立所有資料表。"""
        tables = {
            "Products": """
                CREATE TABLE IF NOT EXISTS Products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    stock_quantity INTEGER NOT NULL,
                    category TEXT
                );
            """,
            "Suppliers": """
                CREATE TABLE IF NOT EXISTS Suppliers (
                    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact_email TEXT,
                    phone TEXT,
                    address TEXT
                );
            """,
            "Product_Suppliers": """
                CREATE TABLE IF NOT EXISTS Product_Suppliers (
                    product_id INTEGER,
                    supplier_id INTEGER,
                    supply_price REAL NOT NULL,
                    PRIMARY KEY (product_id, supplier_id),
                    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE,
                    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id) ON DELETE CASCADE
                );
            """,
            "Customers": """
                CREATE TABLE IF NOT EXISTS Customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT,
                    address TEXT
                );
            """,
            "Orders": """
                CREATE TABLE IF NOT EXISTS Orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
                );
            """,
            "Order_Items": """
                CREATE TABLE IF NOT EXISTS Order_Items (
                    order_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    PRIMARY KEY (order_id, product_id),
                    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE
                );
            """
        }

        self.conn.execute("PRAGMA foreign_keys = ON;") # 啟用外鍵約束
        for table_name, create_sql in tables.items():
            try:
                self.cursor.execute(create_sql)
                self.conn.commit()
                print(f"資料表 '{table_name}' 建立成功或已存在。")
            except sqlite3.Error as e:
                print(f"建立資料表 '{table_name}' 失敗: {e}")

    def close(self):
        """關閉資料庫連接。"""
        if self.conn:
            self.conn.close()
            print("資料庫連接已關閉。")

    # --- 查詢 (Retrieve) ---
    def fetch_all(self, table_name, conditions=None):
        """
        從指定資料表中獲取所有資料。
        可選參數 conditions: 字典，用於 WHERE 子句，例如 {"column": "value"}
        """
        query = f"SELECT * FROM {table_name}"
        if conditions:
            where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
            query += f" WHERE {where_clause}"
            self.cursor.execute(query, list(conditions.values()))
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def fetch_one(self, table_name, conditions):
        """
        從指定資料表中獲取一筆資料。
        conditions: 字典，用於 WHERE 子句，例如 {"column": "value"}
        """
        query = f"SELECT * FROM {table_name}"
        if conditions:
            where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
            query += f" WHERE {where_clause}"
            self.cursor.execute(query, list(conditions.values()))
        else:
            return None # 必須有條件才能精確查詢一筆
        return self.cursor.fetchone()

    # --- 新增 (Insert) ---
    def insert_data(self, table_name, data):
        """
        向指定資料表插入一筆新資料。
        data: 字典，鍵為欄位名稱，值為對應資料。
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.values()])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            self.cursor.execute(query, list(data.values()))
            self.conn.commit()
            print(f"資料成功插入到 '{table_name}'。ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"插入資料到 '{table_name}' 失敗: {e}")
            return None

    # --- 更新 (Update) ---
    def update_data(self, table_name, data, conditions):
        """
        更新指定資料表中的資料。
        data: 字典，要更新的欄位及其新值。
        conditions: 字典，用於 WHERE 子句，指定要更新的行。
        """
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(conditions.values())
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            print(f"成功更新 '{table_name}' 中的 {self.cursor.rowcount} 筆資料。")
            return self.cursor.rowcount
        except sqlite3.Error as e:
            print(f"更新資料到 '{table_name}' 失敗: {e}")
            return None

    # --- 刪除 (Delete) ---
    def delete_data(self, table_name, conditions):
        """
        從指定資料表中刪除資料。
        conditions: 字典，用於 WHERE 子句，指定要刪除的行。
        """
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        try:
            self.cursor.execute(query, list(conditions.values()))
            self.conn.commit()
            print(f"成功從 '{table_name}' 中刪除 {self.cursor.rowcount} 筆資料。")
            return self.cursor.rowcount
        except sqlite3.Error as e:
            print(f"刪除資料從 '{table_name}' 失敗: {e}")
            return None

    # --- 帶有事務概念的修改 (Transaction Example) ---
    def add_order_and_items_transaction(self, customer_id, product_details):
        """
        事務範例：新增一筆訂單及其多個訂單明細。
        如果訂單明細無法成功新增（例如商品庫存不足），則整筆訂單都不會被新增。

        customer_id: 顧客ID
        product_details: 列表，每個元素為字典 {'product_id': id, 'quantity': qty}
        """
        try:
            # 開始事務
            self.conn.execute("BEGIN TRANSACTION;")

            # 1. 計算訂單總金額並檢查庫存
            total_amount = 0
            # 儲存更新庫存的資訊
            stock_updates = []
            for item in product_details:
                product_id = item['product_id']
                quantity = item['quantity']

                # 獲取商品資訊以檢查庫存和獲取價格
                product_info = self.fetch_one("Products", {"product_id": product_id})
                if not product_info:
                    raise ValueError(f"商品 ID {product_id} 不存在。")

                product_name, description, price, stock_quantity, category = product_info[1:] # 假設欄位順序

                if stock_quantity < quantity:
                    raise ValueError(f"商品 '{product_name}' (ID: {product_id}) 庫存不足。目前庫存: {stock_quantity}, 需求: {quantity}")

                total_amount += price * quantity
                stock_updates.append({'product_id': product_id, 'new_stock': stock_quantity - quantity})

            # 2. 新增訂單主資訊
            order_data = {
                "customer_id": customer_id,
                "order_date": datetime.now().isoformat(),
                "status": "處理中",
                "total_amount": total_amount
            }
            self.cursor.execute(
                "INSERT INTO Orders (customer_id, order_date, status, total_amount) VALUES (?, ?, ?, ?)",
                (order_data["customer_id"], order_data["order_date"], order_data["status"], order_data["total_amount"])
            )
            order_id = self.cursor.lastrowid
            if not order_id:
                raise Exception("無法新增訂單主資訊。")

            # 3. 新增訂單明細並更新商品庫存
            for item in product_details:
                product_id = item['product_id']
                quantity = item['quantity']
                # 重新獲取商品價格，確保使用訂單生成時的最新價格
                product_price_at_order = self.fetch_one("Products", {"product_id": product_id})[3] # price is at index 3

                self.cursor.execute(
                    "INSERT INTO Order_Items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, product_id, quantity, product_price_at_order)
                )

                # 更新商品庫存
                new_stock_qty = next(s['new_stock'] for s in stock_updates if s['product_id'] == product_id)
                self.cursor.execute(
                    "UPDATE Products SET stock_quantity = ? WHERE product_id = ?",
                    (new_stock_qty, product_id)
                )

            # 提交事務
            self.conn.commit()
            print(f"成功新增訂單 (ID: {order_id}) 及其訂單明細，並更新商品庫存。")
            return order_id

        except ValueError as ve:
            self.conn.rollback()
            print(f"事務失敗 (資料錯誤): {ve}")
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"事務失敗 (操作錯誤): {e}")
            return None

# --- 使用範例 ---
if __name__ == "__main__":
    db = OnlineShoppingDB()

    print("\n--- 1. 插入初始資料 ---")
    # 插入商品
    product1_id = db.insert_data("Products", {
        "name": "無線藍牙耳機", "description": "高音質、舒適配戴",
        "price": 999.0, "stock_quantity": 50, "category": "電子產品"
    })
    product2_id = db.insert_data("Products", {
        "name": "機械式鍵盤", "description": "青軸，手感極佳",
        "price": 1200.0, "stock_quantity": 30, "category": "電腦週邊"
    })
    product3_id = db.insert_data("Products", {
        "name": "人體工學滑鼠", "description": "緩解手腕疲勞",
        "price": 450.0, "stock_quantity": 100, "category": "電腦週邊"
    })

    # 插入供應商
    supplier1_id = db.insert_data("Suppliers", {
        "name": "XYZ 電子", "contact_email": "info@xyz.com",
        "phone": "02-12345678", "address": "台北市科技大道1號"
    })
    supplier2_id = db.insert_data("Suppliers", {
        "name": "ABC 周邊", "contact_email": "support@abc.com",
        "phone": "03-87654321", "address": "新北市創新園區2號"
    })

    # 插入商品與供應商關聯
    if product1_id and supplier1_id:
        db.insert_data("Product_Suppliers", {"product_id": product1_id, "supplier_id": supplier1_id, "supply_price": 750.0})
    if product2_id and supplier2_id:
        db.insert_data("Product_Suppliers", {"product_id": product2_id, "supplier_id": supplier2_id, "supply_price": 900.0})
    if product3_id and supplier2_id:
        db.insert_data("Product_Suppliers", {"product_id": product3_id, "supplier_id": supplier2_id, "supply_price": 300.0})


    # 插入顧客
    customer1_id = db.insert_data("Customers", {
        "name": "王小明", "email": "xiaoming@example.com",
        "password": "hashed_password_1", "phone": "0912-345678", "address": "台中市西區民生路"
    })
    customer2_id = db.insert_data("Customers", {
        "name": "陳美麗", "email": "meili@example.com",
        "password": "hashed_password_2", "phone": "0987-654321", "address": "高雄市左營區勝利路"
    })

    print("\n--- 2. 查詢資料範例 ---")
    print("所有商品：", db.fetch_all("Products"))
    print("所有顧客：", db.fetch_all("Customers"))
    print("查詢特定商品 (ID 1)：", db.fetch_one("Products", {"product_id": product1_id}))
    print("查詢特定顧客 (email: xiaoming@example.com)：", db.fetch_one("Customers", {"email": "xiaoming@example.com"}))

    print("\n--- 3. 更新資料範例 ---")
    # 更新商品價格
    if product1_id:
        db.update_data("Products", {"price": 950.0}, {"product_id": product1_id})
    # 更新顧客地址
    if customer1_id:
        db.update_data("Customers", {"address": "台中市南屯區公益路"}, {"customer_id": customer1_id})
    print("更新後商品 (ID 1)：", db.fetch_one("Products", {"product_id": product1_id}))
    print("更新後顧客 (ID 1)：", db.fetch_one("Customers", {"customer_id": customer1_id}))


    print("\n--- 4. 帶有事務的修改 (新增訂單及明細) ---")
    # 成功案例：新增一筆包含多個商品的訂單
    if customer1_id and product1_id and product2_id:
        print("\n--- 4.1 成功案例：顧客王小明購買耳機和鍵盤 ---")
        order_details_success = [
            {'product_id': product1_id, 'quantity': 2},
            {'product_id': product2_id, 'quantity': 1}
        ]
        new_order_id_success = db.add_order_and_items_transaction(customer1_id, order_details_success)
        if new_order_id_success:
            print(f"成功新增的訂單 ID: {new_order_id_success}")
            print("查看新訂單：", db.fetch_one("Orders", {"order_id": new_order_id_success}))
            print("查看訂單明細：", db.fetch_all("Order_Items", {"order_id": new_order_id_success}))
            print("查看商品庫存 (耳機):", db.fetch_one("Products", {"product_id": product1_id}))
            print("查看商品庫存 (鍵盤):", db.fetch_one("Products", {"product_id": product2_id}))
        else:
            print("訂單新增失敗。")


    # 失敗案例：商品庫存不足
    if customer2_id and product3_id:
        print("\n--- 4.2 失敗案例：顧客陳美麗購買大量滑鼠導致庫存不足 ---")
        # 假設 product3_id 的庫存是 100，我們嘗試購買 150
        order_details_fail_stock = [
            {'product_id': product3_id, 'quantity': 150}
        ]
        new_order_id_fail_stock = db.add_order_and_items_transaction(customer2_id, order_details_fail_stock)
        if not new_order_id_fail_stock:
            print("訂單因庫存不足而未能新增 (預期結果)。")
            print("查看商品庫存 (滑鼠)，應該沒變:", db.fetch_one("Products", {"product_id": product3_id}))


    # 失敗案例：商品ID不存在
    if customer1_id:
        print("\n--- 4.3 失敗案例：顧客王小明購買不存在的商品 ---")
        order_details_fail_product = [
            {'product_id': 9999, 'quantity': 1} # 假設 9999 是不存在的商品 ID
        ]
        new_order_id_fail_product = db.add_order_and_items_transaction(customer1_id, order_details_fail_product)
        if not new_order_id_fail_product:
            print("訂單因商品不存在而未能新增 (預期結果)。")


    print("\n--- 5. 刪除資料範例 ---")
    # 刪除特定商品 (例如 Product ID 3)
    if product3_id:
        db.delete_data("Products", {"product_id": product3_id})
        print("刪除後所有商品：", db.fetch_all("Products"))


    db.close()