import datetime as dt
import hashlib
import sqlite3
from pathlib import Path
from tkinter import END, LEFT, RIGHT, VERTICAL, Y, filedialog, messagebox, simpledialog, ttk
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk


ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "urban_gear.db"
IMG_DIR = ROOT / "item_images"
RES_DIR = ROOT / "resources"
PLACEHOLDER = RES_DIR / "placeholder.png"


def digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def prepare_placeholder() -> None:
    RES_DIR.mkdir(exist_ok=True)
    if PLACEHOLDER.exists():
        return
    img = Image.new("RGB", (300, 200), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 292, 192), outline=(70, 70, 70), width=3)
    draw.text((95, 90), "URBAN GEAR", fill=(40, 40, 40))
    img.save(PLACEHOLDER)


def setup_database() -> None:
    IMG_DIR.mkdir(exist_ok=True)
    prepare_placeholder()
    con = db()
    cur = con.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
          account_id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          pass_hash TEXT NOT NULL,
          fio TEXT NOT NULL,
          role_code TEXT NOT NULL CHECK (role_code IN ('client','manager','admin'))
        );

        CREATE TABLE IF NOT EXISTS vendors (
          vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS makers (
          maker_id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS groups (
          group_id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS measures (
          measure_id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS stock_items (
          item_id INTEGER PRIMARY KEY AUTOINCREMENT,
          sku TEXT NOT NULL UNIQUE,
          item_name TEXT NOT NULL,
          group_id INTEGER NOT NULL,
          about TEXT NOT NULL DEFAULT '',
          maker_id INTEGER NOT NULL,
          vendor_id INTEGER NOT NULL,
          base_price REAL NOT NULL CHECK(base_price >= 0),
          measure_id INTEGER NOT NULL,
          qty INTEGER NOT NULL CHECK(qty >= 0),
          promo REAL NOT NULL DEFAULT 0 CHECK(promo >= 0 AND promo <= 100),
          photo_path TEXT,
          FOREIGN KEY(group_id) REFERENCES groups(group_id),
          FOREIGN KEY(maker_id) REFERENCES makers(maker_id),
          FOREIGN KEY(vendor_id) REFERENCES vendors(vendor_id),
          FOREIGN KEY(measure_id) REFERENCES measures(measure_id)
        );

        CREATE TABLE IF NOT EXISTS order_states (
          state_id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS pickup_locations (
          location_id INTEGER PRIMARY KEY AUTOINCREMENT,
          address TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS sales_orders (
          order_id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_code TEXT NOT NULL UNIQUE,
          customer_name TEXT NOT NULL,
          state_id INTEGER NOT NULL,
          location_id INTEGER NOT NULL,
          created_on TEXT NOT NULL,
          issued_on TEXT NOT NULL,
          FOREIGN KEY(state_id) REFERENCES order_states(state_id),
          FOREIGN KEY(location_id) REFERENCES pickup_locations(location_id)
        );

        CREATE TABLE IF NOT EXISTS sales_order_rows (
          row_id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_id INTEGER NOT NULL,
          item_id INTEGER NOT NULL,
          qty INTEGER NOT NULL CHECK(qty > 0),
          unit_price REAL NOT NULL CHECK(unit_price >= 0),
          FOREIGN KEY(order_id) REFERENCES sales_orders(order_id) ON DELETE CASCADE,
          FOREIGN KEY(item_id) REFERENCES stock_items(item_id)
        );
        """
    )

    cur.executemany(
        "INSERT OR IGNORE INTO accounts(username, pass_hash, fio, role_code) VALUES (?, ?, ?, ?)",
        [
            ("root", digest("root123"), "Орлова Мария Николаевна", "admin"),
            ("boss", digest("boss123"), "Романов Денис Игоревич", "manager"),
            ("buyer", digest("buyer123"), "Кузнецова Ирина Павловна", "client"),
        ],
    )

    for table, col, values in [
        ("vendors", "title", ["Север Логистик", "Prime Supply", "City Stock"]),
        ("makers", "title", ["Urban", "Altitude", "Core"]),
        ("groups", "title", ["Куртки", "Рюкзаки", "Кроссовки"]),
        ("measures", "title", ["шт."]),
        ("order_states", "title", ["Новый", "Собирается", "Выдан"]),
        (
            "pickup_locations",
            "address",
            ["г. Москва, ул. Ленина, 10", "г. Казань, ул. Баумана, 5"],
        ),
    ]:
        cur.executemany(
            f"INSERT OR IGNORE INTO {table}({col}) VALUES (?)",
            [(v,) for v in values],
        )

    cur.executemany(
        """
        INSERT OR IGNORE INTO stock_items(sku, item_name, group_id, about, maker_id, vendor_id, base_price, measure_id, qty, promo, photo_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("UG-A101", "Куртка Storm", 1, "Ветрозащитная куртка", 1, 1, 7990, 1, 5, 10, str(PLACEHOLDER)),
            ("UG-A115", "Куртка Polar", 1, "Зимняя куртка", 2, 1, 9990, 1, 3, 7, str(PLACEHOLDER)),
            ("UG-A140", "Куртка City", 1, "Легкая городская куртка", 3, 2, 6490, 1, 12, 0, str(PLACEHOLDER)),
            ("UG-B210", "Рюкзак Metro", 2, "Городской рюкзак 20л", 2, 2, 3990, 1, 0, 18, str(PLACEHOLDER)),
            ("UG-B240", "Рюкзак Trail", 2, "Треккинговый рюкзак 35л", 1, 3, 6590, 1, 6, 12, str(PLACEHOLDER)),
            ("UG-B290", "Сумка Sling", 2, "Компактная сумка через плечо", 3, 1, 2790, 1, 14, 0, str(PLACEHOLDER)),
            ("UG-C330", "Кроссовки Dash", 3, "Повседневные кроссовки", 3, 3, 5990, 1, 8, 5, str(PLACEHOLDER)),
            ("UG-C350", "Кроссовки Sprint", 3, "Беговая модель", 2, 2, 7290, 1, 4, 16, str(PLACEHOLDER)),
            ("UG-C390", "Кеды Street", 3, "Классические кеды", 1, 1, 4890, 1, 9, 0, str(PLACEHOLDER)),
            ("UG-C420", "Кроссовки Aero", 3, "Легкие кроссовки", 2, 3, 8190, 1, 2, 20, str(PLACEHOLDER)),
        ],
    )

    count_orders = cur.execute("SELECT COUNT(*) c FROM sales_orders").fetchone()["c"]
    if count_orders == 0:
        state_map = {
            row["title"]: row["state_id"]
            for row in cur.execute("SELECT state_id, title FROM order_states").fetchall()
        }
        location_map = {
            row["address"]: row["location_id"]
            for row in cur.execute("SELECT location_id, address FROM pickup_locations").fetchall()
        }

        cur.executemany(
            """
            INSERT INTO sales_orders(order_code, customer_name, state_id, location_id, created_on, issued_on)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("SO-2026-001", "Климова Елена", state_map["Новый"], location_map["г. Москва, ул. Ленина, 10"], "2026-02-20", "2026-02-23"),
                ("SO-2026-002", "Астахов Иван", state_map["Собирается"], location_map["г. Казань, ул. Баумана, 5"], "2026-02-21", "2026-02-24"),
                ("SO-2026-003", "Воробьева Марина", state_map["Выдан"], location_map["г. Москва, ул. Ленина, 10"], "2026-02-18", "2026-02-22"),
            ],
        )

        item_map = {
            row["sku"]: row["item_id"]
            for row in cur.execute("SELECT item_id, sku FROM stock_items").fetchall()
        }
        order_map = {
            row["order_code"]: row["order_id"]
            for row in cur.execute("SELECT order_id, order_code FROM sales_orders").fetchall()
        }

        cur.executemany(
            """
            INSERT INTO sales_order_rows(order_id, item_id, qty, unit_price)
            VALUES (?, ?, ?, ?)
            """,
            [
                (order_map["SO-2026-001"], item_map["UG-A101"], 1, 7990),
                (order_map["SO-2026-001"], item_map["UG-B240"], 1, 6590),
                (order_map["SO-2026-002"], item_map["UG-C350"], 2, 7290),
                (order_map["SO-2026-002"], item_map["UG-B290"], 1, 2790),
                (order_map["SO-2026-003"], item_map["UG-C390"], 1, 4890),
            ],
        )

    con.commit()
    con.close()


def save_item_image(path: str, old: str | None = None) -> str:
    IMG_DIR.mkdir(exist_ok=True)
    img = Image.open(path).convert("RGB").resize((300, 200))
    out = IMG_DIR / f"item_{dt.datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
    img.save(out, "PNG")
    if old:
        old_path = Path(old)
        if old_path.exists() and old_path.parent == IMG_DIR:
            old_path.unlink(missing_ok=True)
    return str(out)


class UrbanGearApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ООО Обувь")
        self.geometry("1240x760")
        self.setup_styles()
        self.current_user = None
        self.active = None
        self.open_login()

    def setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("UG.Treeview", rowheight=58, font=("Segoe UI", 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("UG.Treeview.Heading", background="#2E8B57", foreground="white", font=("Segoe UI", 9, "bold"))
        style.map("UG.Treeview.Heading", background=[("active", "#72f700")], foreground=[("active", "black")])

        style.configure("UGO.Treeview", rowheight=32, font=("Segoe UI", 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("UGO.Treeview.Heading", background="#2E8B57", foreground="white", font=("Segoe UI", 9, "bold"))
        style.map("UGO.Treeview.Heading", background=[("active", "#72f700")], foreground=[("active", "black")])

        style.configure("UGR.Treeview", rowheight=28, font=("Segoe UI", 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("UGR.Treeview.Heading", background="#2E8B57", foreground="white", font=("Segoe UI", 9, "bold"))
        style.map("UGR.Treeview.Heading", background=[("active", "#72f700")], foreground=[("active", "black")])

    def set_screen(self, frame: tk.Frame) -> None:
        if self.active is not None:
            self.active.destroy()
        self.active = frame
        self.active.pack(fill="both", expand=True)

    def open_login(self) -> None:
        self.current_user = None
        self.set_screen(LoginScreen(self))

    def open_catalog(self, user: dict) -> None:
        self.current_user = user
        self.set_screen(CatalogScreen(self, user))

    def open_orders(self, user: dict) -> None:
        self.current_user = user
        self.set_screen(OrdersScreen(self, user))


class LoginScreen(tk.Frame):
    def __init__(self, app: UrbanGearApp) -> None:
        super().__init__(app, padx=24, pady=24, bg="#efefef")
        self.app = app

        tk.Label(self, text="ООО Обувь", font=("Segoe UI", 32, "bold"), fg="#2E8B57", bg="#efefef").pack(pady=(70, 4))
        tk.Label(self, text="Авторизация пользователя", font=("Segoe UI", 12), bg="#efefef", fg="#5f5f5f").pack(pady=(0, 18))

        box = tk.Frame(self, bg="#efefef")
        box.pack()
        tk.Label(box, text="Логин", bg="#efefef").grid(row=0, column=0, sticky="w", pady=6)
        tk.Label(box, text="Пароль", bg="#efefef").grid(row=1, column=0, sticky="w", pady=6)
        self.username = tk.Entry(box, width=36)
        self.password = tk.Entry(box, width=36, show="*")
        self.username.grid(row=0, column=1, pady=6, padx=8)
        self.password.grid(row=1, column=1, pady=6, padx=8)

        btns = tk.Frame(self, bg="#efefef")
        btns.pack(pady=12)
        tk.Button(btns, text="Войти", width=32, command=self.sign_in).pack(pady=4)
        tk.Button(btns, text="Гостевой вход", width=32, bg="#28f08c", command=self.as_guest).pack(pady=4)
        tk.Button(btns, text="Инициализировать БД", width=32, bg="#72f700", command=self.init_db_click).pack(pady=4)

    def init_db_click(self) -> None:
        setup_database()
        messagebox.showinfo("Готово", "База данных инициализирована")

    def as_guest(self) -> None:
        self.app.open_catalog({"fio": "Гость", "role_code": "guest"})

    def sign_in(self) -> None:
        username = self.username.get().strip()
        password = self.password.get().strip()
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        con = db()
        user = con.execute(
            "SELECT account_id, fio, role_code FROM accounts WHERE username=? AND pass_hash=?",
            (username, digest(password)),
        ).fetchone()
        con.close()
        if not user:
            messagebox.showerror("Ошибка", "Неверные учетные данные")
            return
        self.app.open_catalog(dict(user))


class CatalogScreen(tk.Frame):
    def __init__(self, app: UrbanGearApp, user: dict) -> None:
        super().__init__(app, padx=10, pady=10)
        self.app = app
        self.user = user
        self.search = tk.StringVar()
        self.sort = tk.StringVar(value="Без сортировки")
        self.vendor = tk.StringVar(value="Все поставщики")
        self.vendor_map = {"Все поставщики": None}
        self.images = []
        self.edit_open = False

        self.build_header()
        self.build_filters()
        self.build_table()
        self.load_vendors()
        self.refresh()

    def build_header(self) -> None:
        top = tk.Frame(self, bg="#f8fbf3")
        top.pack(fill="x")
        left_panel = tk.Frame(top, bg="#f8fbf3")
        left_panel.pack(side=LEFT, fill="x", expand=True)
        tk.Label(left_panel, text="Каталог ООО Обувь", font=("Segoe UI", 24, "bold"), bg="#f8fbf3").pack(anchor="w", padx=8, pady=(6, 0))
        self.info_lbl = tk.Label(left_panel, text="", bg="#f8fbf3")
        self.info_lbl.pack(anchor="w", padx=8, pady=(0, 6))

        right_panel = tk.Frame(top, bg="#f8fbf3")
        right_panel.pack(side=RIGHT, padx=8, pady=6)
        tk.Button(right_panel, text="Выход", command=self.app.open_login, width=12).pack(anchor="e")
        tk.Label(right_panel, text=f"Пользователь:\n{self.user['fio']}", bg="#f8fbf3", justify="right", anchor="e").pack(anchor="e", pady=(6, 0))

    def build_filters(self) -> None:
        row = tk.LabelFrame(self, text="Панель фильтров и действий", padx=8, pady=8)
        row.pack(fill="x", pady=(10, 12), padx=4)
        role = self.user["role_code"]

        left_controls = tk.Frame(row)
        left_controls.pack(side=LEFT, fill="x", expand=True, padx=(6, 10), pady=4)

        if role in ("manager", "admin"):
            tk.Label(left_controls, text="Поиск:").pack(side=LEFT, padx=(6, 4))
            tk.Entry(left_controls, textvariable=self.search, width=22).pack(side=LEFT, padx=6)
            tk.Label(left_controls, text="Сортировка:").pack(side=LEFT, padx=(12, 4))
            ttk.Combobox(
                left_controls,
                textvariable=self.sort,
                state="readonly",
                width=18,
                values=["Без сортировки", "Остаток ↑", "Остаток ↓"],
            ).pack(side=LEFT, padx=6)
            tk.Label(left_controls, text="Поставщик:").pack(side=LEFT, padx=(12, 4))
            self.vendor_combo = ttk.Combobox(left_controls, textvariable=self.vendor, state="readonly", width=22)
            self.vendor_combo.pack(side=LEFT, padx=6)
            self.search.trace_add("write", lambda *_: self.refresh())
            self.sort.trace_add("write", lambda *_: self.refresh())
            self.vendor.trace_add("write", lambda *_: self.refresh())

        right_actions = tk.Frame(row)
        right_actions.pack(side=RIGHT, padx=(10, 6), pady=4)

        if role == "admin":
            tk.Button(right_actions, text="Новый товар", bg="#72f700", command=self.add_item).pack(side=LEFT, padx=4)
            tk.Button(right_actions, text="Изменить", command=self.edit_item).pack(side=LEFT, padx=4)
            tk.Button(right_actions, text="Удалить", command=self.delete_item).pack(side=LEFT, padx=4)
            tk.Button(right_actions, text="Новый поставщик", command=self.add_vendor).pack(side=LEFT, padx=4)

        if role in ("manager", "admin"):
            tk.Button(right_actions, text="Заказы", bg="#28f08c", command=lambda: self.app.open_orders(self.user)).pack(side=LEFT, padx=8)

    def build_table(self) -> None:
        wrap = tk.LabelFrame(self, text="Список товаров", padx=4, pady=4)
        wrap.pack(fill="both", expand=True, padx=4, pady=(0, 6))
        cols = (
            "item_id", "sku", "item_name", "group", "about", "maker", "vendor", "price", "final", "qty", "promo"
        )
        self.table = ttk.Treeview(wrap, columns=cols, show="tree headings", style="UG.Treeview")
        self.table.heading("#0", text="Изображение")
        self.table.column("#0", width=84, stretch=False, anchor="center")
        for col, title, width in [
            ("item_id", "ID", 50),
            ("sku", "Артикул", 95),
            ("item_name", "Наименование", 150),
            ("group", "Категория", 110),
            ("about", "Характеристики", 180),
            ("maker", "Производитель", 120),
            ("vendor", "Поставщик", 130),
            ("price", "Базовая цена", 95),
            ("final", "Цена со скидкой", 115),
            ("qty", "Остаток на складе", 120),
            ("promo", "Скидка, %", 85),
        ]:
            self.table.heading(col, text=title, anchor="center")
            self.table.column(col, width=width, anchor="w")

        self.table.heading("#0", text="Изображение", anchor="center")
        self.table.tag_configure("high", background="#2E8B57", foreground="white")
        self.table.tag_configure("zero", background="#ADD8E6")
        self.table.tag_configure("odd", background="#f5f5f5")
        self.table.tag_configure("even", background="#ffffff")
        self.table.pack(side=LEFT, fill="both", expand=True)
        ttk.Scrollbar(wrap, orient=VERTICAL, command=self.table.yview).pack(side=RIGHT, fill=Y)
        self.table.configure(yscrollcommand=lambda f, l: None)

    def load_vendors(self) -> None:
        if self.user["role_code"] not in ("manager", "admin"):
            return
        con = db()
        rows = con.execute("SELECT vendor_id, title FROM vendors ORDER BY title").fetchall()
        con.close()
        self.vendor_map = {"Все поставщики": None}
        for row in rows:
            self.vendor_map[row["title"]] = row["vendor_id"]
        self.vendor_combo["values"] = list(self.vendor_map.keys())

    def refresh(self) -> None:
        role = self.user["role_code"]
        con = db()
        query = (
            "SELECT si.item_id, si.sku, si.item_name, g.title group_title, si.about, mk.title maker_title, vd.title vendor_title, "
            "si.base_price, si.promo, ROUND(si.base_price*(1-si.promo/100.0),2) final_price, si.qty, si.photo_path "
            "FROM stock_items si "
            "JOIN groups g ON g.group_id=si.group_id "
            "JOIN makers mk ON mk.maker_id=si.maker_id "
            "JOIN vendors vd ON vd.vendor_id=si.vendor_id"
        )
        where, params = [], []
        if role in ("manager", "admin"):
            text = self.search.get().strip().lower()
            vend = self.vendor_map.get(self.vendor.get())
            if text:
                where.append("(lower(si.sku) LIKE ? OR lower(si.item_name) LIKE ? OR lower(g.title) LIKE ? OR lower(si.about) LIKE ? OR lower(mk.title) LIKE ? OR lower(vd.title) LIKE ?)")
                params.extend([f"%{text}%"] * 6)
            if vend:
                where.append("si.vendor_id = ?")
                params.append(vend)
        if where:
            query += " WHERE " + " AND ".join(where)
        if role in ("manager", "admin") and self.sort.get() == "Остаток ↑":
            query += " ORDER BY si.qty ASC"
        elif role in ("manager", "admin") and self.sort.get() == "Остаток ↓":
            query += " ORDER BY si.qty DESC"
        else:
            query += " ORDER BY si.item_id"
        rows = con.execute(query, params).fetchall()
        con.close()

        total_count = len(rows)
        low_count = len([r for r in rows if r["qty"] == 0])
        promo_count = len([r for r in rows if r["promo"] > 15])
        self.info_lbl.configure(text=f"Позиций: {total_count} | Нет в наличии: {low_count} | Скидка >15%: {promo_count}")

        self.table.delete(*self.table.get_children())
        self.images = []
        for idx, row in enumerate(rows):
            img_path = Path(row["photo_path"] or str(PLACEHOLDER))
            if not img_path.exists():
                img_path = PLACEHOLDER
            thumb = ImageTk.PhotoImage(Image.open(img_path).convert("RGB").resize((46, 46)))
            self.images.append(thumb)

            tag = "high" if row["promo"] > 15 else "zero" if row["qty"] == 0 else ("even" if idx % 2 == 0 else "odd")
            self.table.insert(
                "",
                END,
                image=thumb,
                values=(
                    row["item_id"], row["sku"], row["item_name"], row["group_title"], row["about"],
                    row["maker_title"], row["vendor_title"], f"{row['base_price']:.2f}", f"{row['final_price']:.2f}",
                    row["qty"], f"{int(row['promo'])}%"
                ),
                tags=(tag,),
            )

    def selected_id(self) -> int | None:
        sel = self.table.selection()
        if not sel:
            return None
        return int(self.table.item(sel[0], "values")[0])

    def add_vendor(self) -> None:
        name = simpledialog.askstring("Поставщик", "Введите название поставщика:", parent=self)
        if not name:
            return
        try:
            con = db()
            con.execute("INSERT INTO vendors(title) VALUES (?)", (name.strip(),))
            con.commit()
            con.close()
            self.load_vendors()
            messagebox.showinfo("Готово", "Поставщик добавлен")
        except sqlite3.IntegrityError:
            messagebox.showwarning("Внимание", "Такой поставщик уже есть")

    def add_item(self) -> None:
        if self.edit_open:
            messagebox.showwarning("Внимание", "Форма уже открыта")
            return
        self.edit_open = True
        ItemForm(self, None)

    def edit_item(self) -> None:
        item_id = self.selected_id()
        if not item_id:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        if self.edit_open:
            messagebox.showwarning("Внимание", "Форма уже открыта")
            return
        self.edit_open = True
        ItemForm(self, item_id)

    def delete_item(self) -> None:
        item_id = self.selected_id()
        if not item_id:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        con = db()
        link = con.execute("SELECT COUNT(*) c FROM sales_order_rows WHERE item_id=?", (item_id,)).fetchone()["c"]
        if link:
            con.close()
            messagebox.showerror("Ошибка", "Нельзя удалить: товар используется в заказах")
            return
        row = con.execute("SELECT photo_path FROM stock_items WHERE item_id=?", (item_id,)).fetchone()
        con.execute("DELETE FROM stock_items WHERE item_id=?", (item_id,))
        con.commit()
        con.close()
        if row and row["photo_path"]:
            path = Path(row["photo_path"])
            if path.exists() and path.parent == IMG_DIR:
                path.unlink(missing_ok=True)
        self.refresh()


class ItemForm(tk.Toplevel):
    def __init__(self, parent: CatalogScreen, item_id: int | None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.item_id = item_id
        self.old_img = None
        self.new_img = None
        self.preview = None
        self.maps = {}
        self.title("Товар ООО Обувь")
        self.geometry("860x730")
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.fields = {}
        self.build()
        self.load_refs()
        if item_id:
            self.load_item(item_id)

    def close(self) -> None:
        self.parent.edit_open = False
        self.destroy()

    def build(self) -> None:
        tk.Label(self, text="Карточка товара", font=("Segoe UI", 20, "bold")).pack(pady=8)

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=20, pady=8)

        left = tk.LabelFrame(body, text="Фото и описание", padx=10, pady=10)
        left.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))
        self.preview_label = tk.Label(left)
        self.preview_label.pack(pady=6)
        tk.Button(left, text="Загрузить фото", command=self.pick_image).pack(fill="x", pady=(0, 8))

        tk.Label(left, text="Описание").pack(anchor="w")
        about_entry = tk.Entry(left, width=42)
        about_entry.pack(fill="x", pady=4)
        self.fields["about"] = about_entry

        right = tk.LabelFrame(body, text="Параметры товара", padx=10, pady=10)
        right.pack(side=LEFT, fill="both", expand=True, padx=(8, 0))
        rows = [
            ("sku", "SKU", "entry"),
            ("name", "Название", "entry"),
            ("group", "Группа", "combo"),
            ("maker", "Бренд", "combo"),
            ("vendor", "Поставщик", "combo"),
            ("measure", "Ед.изм.", "combo"),
            ("price", "Цена", "entry"),
            ("qty", "Остаток", "entry"),
            ("promo", "Скидка", "entry"),
        ]
        for i, (key, title, kind) in enumerate(rows):
            tk.Label(right, text=title, width=14, anchor="w").grid(row=i, column=0, pady=5, sticky="w")
            if kind == "combo":
                w = ttk.Combobox(right, width=30, state="readonly")
            else:
                w = tk.Entry(right, width=33)
            w.grid(row=i, column=1, pady=5, sticky="w")
            self.fields[key] = w

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=20, pady=(4, 10))
        tk.Button(btns, text="Сохранить", bg="#72f700", command=self.save).pack(side=LEFT, expand=True, fill="x", padx=2)
        tk.Button(btns, text="Отмена", command=self.close).pack(side=LEFT, expand=True, fill="x", padx=2)

    def load_refs(self) -> None:
        con = db()
        refs = {
            "group": ("groups", "group_id", "title"),
            "maker": ("makers", "maker_id", "title"),
            "vendor": ("vendors", "vendor_id", "title"),
            "measure": ("measures", "measure_id", "title"),
        }
        for key, (table, id_col, val_col) in refs.items():
            rows = con.execute(f"SELECT {id_col} idv, {val_col} vv FROM {table} ORDER BY vv").fetchall()
            self.maps[key] = {r["vv"]: r["idv"] for r in rows}
            combo: ttk.Combobox = self.fields[key]  # type: ignore
            combo["values"] = list(self.maps[key].keys())
            if combo["values"]:
                combo.current(0)
        con.close()
        self.show_preview(str(PLACEHOLDER))

    def load_item(self, item_id: int) -> None:
        con = db()
        row = con.execute(
            """
            SELECT si.*, g.title gt, mk.title mt, vd.title vt, ms.title ust
            FROM stock_items si
            JOIN groups g ON g.group_id=si.group_id
            JOIN makers mk ON mk.maker_id=si.maker_id
            JOIN vendors vd ON vd.vendor_id=si.vendor_id
            JOIN measures ms ON ms.measure_id=si.measure_id
            WHERE si.item_id=?
            """,
            (item_id,),
        ).fetchone()
        con.close()
        if not row:
            self.close()
            return
        self.fields["sku"].insert(0, row["sku"])
        self.fields["name"].insert(0, row["item_name"])
        self.fields["about"].insert(0, row["about"])
        self.fields["price"].insert(0, str(row["base_price"]))
        self.fields["qty"].insert(0, str(row["qty"]))
        self.fields["promo"].insert(0, str(row["promo"]))
        self.fields["group"].set(row["gt"])
        self.fields["maker"].set(row["mt"])
        self.fields["vendor"].set(row["vt"])
        self.fields["measure"].set(row["ust"])
        self.old_img = row["photo_path"]
        self.show_preview(row["photo_path"] or str(PLACEHOLDER))

    def pick_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if not path:
            return
        self.new_img = path
        self.show_preview(path)

    def show_preview(self, path: str) -> None:
        src = Path(path)
        if not src.exists():
            src = PLACEHOLDER
        photo = ImageTk.PhotoImage(Image.open(src).convert("RGB").resize((300, 200)))
        self.preview = photo
        self.preview_label.configure(image=photo)

    def save(self) -> None:
        try:
            sku = self.fields["sku"].get().strip()
            name = self.fields["name"].get().strip()
            about = self.fields["about"].get().strip()
            group_id = self.maps["group"][self.fields["group"].get().strip()]
            maker_id = self.maps["maker"][self.fields["maker"].get().strip()]
            vendor_id = self.maps["vendor"][self.fields["vendor"].get().strip()]
            measure_id = self.maps["measure"][self.fields["measure"].get().strip()]
            price = float(self.fields["price"].get().strip().replace(",", "."))
            qty = int(self.fields["qty"].get().strip())
            promo = float(self.fields["promo"].get().strip().replace(",", "."))

            if not sku or not name:
                raise ValueError("SKU и название обязательны")
            if price < 0 or qty < 0:
                raise ValueError("Цена и остаток не могут быть отрицательными")
            if promo < 0 or promo > 100:
                raise ValueError("Скидка должна быть 0..100")

            path = self.old_img or str(PLACEHOLDER)
            if self.new_img:
                path = save_item_image(self.new_img, self.old_img)

            con = db()
            if self.item_id is None:
                con.execute(
                    """
                    INSERT INTO stock_items(sku, item_name, group_id, about, maker_id, vendor_id, base_price, measure_id, qty, promo, photo_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sku, name, group_id, about, maker_id, vendor_id, price, measure_id, qty, promo, path),
                )
            else:
                con.execute(
                    """
                    UPDATE stock_items
                    SET sku=?, item_name=?, group_id=?, about=?, maker_id=?, vendor_id=?, base_price=?, measure_id=?, qty=?, promo=?, photo_path=?
                    WHERE item_id=?
                    """,
                    (sku, name, group_id, about, maker_id, vendor_id, price, measure_id, qty, promo, path, self.item_id),
                )
            con.commit()
            con.close()
            self.parent.refresh()
            self.close()
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "SKU должен быть уникальным")
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))


class OrdersScreen(tk.Frame):
    def __init__(self, app: UrbanGearApp, user: dict) -> None:
        super().__init__(app, padx=10, pady=10)
        self.app = app
        self.user = user
        self.build_header()
        self.build_actions()
        self.build_table()
        self.refresh()

    def build_header(self) -> None:
        top = tk.Frame(self)
        top.pack(fill="x")
        tk.Label(top, text="Управление заказами", font=("Segoe UI", 22, "bold")).pack(side=LEFT)
        tk.Button(top, text="Назад", command=lambda: self.app.open_catalog(self.user)).pack(side=RIGHT)

    def build_actions(self) -> None:
        row = tk.Frame(self)
        row.pack(fill="x", pady=8)
        if self.user["role_code"] == "admin":
            tk.Button(row, text="Создать заказ", bg="#72f700", command=lambda: OrderForm(self, None)).pack(side=LEFT, padx=4)
            tk.Button(row, text="Изменить", command=self.edit).pack(side=LEFT, padx=4)
            tk.Button(row, text="Удалить", command=self.delete).pack(side=LEFT, padx=4)

    def build_table(self) -> None:
        cols = ("id", "code", "customer", "state", "location", "created", "issued", "total")
        self.table = ttk.Treeview(self, columns=cols, show="headings", style="UGO.Treeview")
        for col, title, width in [
            ("id", "ID", 50), ("code", "Код", 100), ("customer", "Клиент", 160), ("state", "Статус", 110),
            ("location", "Пункт выдачи", 250), ("created", "Дата", 110), ("issued", "Выдача", 110), ("total", "Итого", 90),
        ]:
            self.table.heading(col, text=title, anchor="center")
            self.table.column(col, width=width)
        self.table.tag_configure("odd", background="#f5f5f5")
        self.table.tag_configure("even", background="#ffffff")
        self.table.pack(fill="both", expand=True)

    def refresh(self) -> None:
        con = db()
        rows = con.execute(
            """
            SELECT so.order_id, so.order_code, so.customer_name, st.title state_title, pl.address,
                   so.created_on, so.issued_on,
                   COALESCE(SUM(sr.qty * sr.unit_price), 0) total_sum
            FROM sales_orders so
            JOIN order_states st ON st.state_id = so.state_id
            JOIN pickup_locations pl ON pl.location_id = so.location_id
            LEFT JOIN sales_order_rows sr ON sr.order_id = so.order_id
            GROUP BY so.order_id
            ORDER BY so.order_id DESC
            """
        ).fetchall()
        con.close()
        self.table.delete(*self.table.get_children())
        for idx, row in enumerate(rows):
            self.table.insert(
                "", END,
                values=(row["order_id"], row["order_code"], row["customer_name"], row["state_title"], row["address"], row["created_on"], row["issued_on"], f"{row['total_sum']:.2f}"),
                tags=(("even" if idx % 2 == 0 else "odd"),)
            )

    def selected(self) -> int | None:
        sel = self.table.selection()
        if not sel:
            return None
        return int(self.table.item(sel[0], "values")[0])

    def edit(self) -> None:
        oid = self.selected()
        if not oid:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return
        OrderForm(self, oid)

    def delete(self) -> None:
        oid = self.selected()
        if not oid:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить заказ?"):
            return
        con = db()
        con.execute("DELETE FROM sales_orders WHERE order_id=?", (oid,))
        con.commit()
        con.close()
        self.refresh()


class OrderForm(tk.Toplevel):
    def __init__(self, parent: OrdersScreen, order_id: int | None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.order_id = order_id
        self.items = []
        self.state_map = {}
        self.location_map = {}
        self.item_map = {}
        self.title("Заказ ООО Обувь")
        self.geometry("980x690")

        self.build()
        self.load_refs()
        if order_id:
            self.load_order(order_id)

    def build(self) -> None:
        tk.Label(self, text="Карточка заказа", font=("Segoe UI", 20, "bold")).pack(pady=8)
        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=4)

        form = tk.LabelFrame(body, text="Параметры заказа", padx=10, pady=8)
        form.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))

        self.code = tk.StringVar()
        self.customer = tk.StringVar()
        self.state = tk.StringVar()
        self.location = tk.StringVar()
        self.created = tk.StringVar(value=str(dt.date.today()))
        self.issued = tk.StringVar(value=str(dt.date.today()))

        tk.Label(form, text="Код заказа").grid(row=0, column=0, sticky="w", pady=4)
        tk.Entry(form, textvariable=self.code, width=30).grid(row=0, column=1, sticky="w", pady=4)
        tk.Label(form, text="Клиент").grid(row=1, column=0, sticky="w", pady=4)
        tk.Entry(form, textvariable=self.customer, width=30).grid(row=1, column=1, sticky="w", pady=4)

        tk.Label(form, text="Статус").grid(row=2, column=0, sticky="w", pady=4)
        self.state_combo = ttk.Combobox(form, textvariable=self.state, width=28, state="readonly")
        self.state_combo.grid(row=2, column=1, sticky="w", pady=4)

        tk.Label(form, text="Пункт выдачи").grid(row=3, column=0, sticky="w", pady=4)
        self.location_combo = ttk.Combobox(form, textvariable=self.location, width=45, state="readonly")
        self.location_combo.grid(row=3, column=1, columnspan=3, sticky="w", pady=4)

        tk.Label(form, text="Дата заказа").grid(row=4, column=0, sticky="w", pady=4)
        tk.Entry(form, textvariable=self.created, width=18).grid(row=4, column=1, sticky="w", pady=4)
        tk.Label(form, text="Дата выдачи").grid(row=4, column=2, sticky="w", pady=4)
        tk.Entry(form, textvariable=self.issued, width=18).grid(row=4, column=3, sticky="w", pady=4)

        side = tk.LabelFrame(body, text="Товары в заказ", padx=8, pady=6)
        side.pack(side=LEFT, fill="both", expand=True, padx=(8, 0))

        items_row = tk.Frame(side)
        items_row.pack(fill="x", pady=2)
        self.pick_item = tk.StringVar()
        self.pick_qty = tk.StringVar(value="1")
        self.item_combo = ttk.Combobox(items_row, textvariable=self.pick_item, state="readonly", width=40)
        self.item_combo.pack(side=LEFT, padx=2)
        tk.Spinbox(items_row, from_=1, to=999, textvariable=self.pick_qty, width=8).pack(side=LEFT, padx=2)
        tk.Button(items_row, text="Добавить", bg="#28f08c", command=self.add_row).pack(side=LEFT, padx=4)

        self.rows = ttk.Treeview(self, columns=("sku", "name", "qty", "sum"), show="headings", height=10, style="UGR.Treeview")
        for c, t, w in [("sku", "SKU", 120), ("name", "Товар", 440), ("qty", "Кол-во", 100), ("sum", "Сумма", 120)]:
            self.rows.heading(c, text=t, anchor="center")
            self.rows.column(c, width=w)
        self.rows.tag_configure("odd", background="#f5f5f5")
        self.rows.tag_configure("even", background="#ffffff")
        self.rows.pack(fill="both", expand=True, pady=6)
        tk.Button(side, text="Удалить позицию", command=self.remove_row).pack(anchor="w", pady=4)

        self.total_lbl = tk.Label(self, text="Итого: 0.00", font=("Segoe UI", 14, "bold"))
        self.total_lbl.pack(anchor="e", padx=16, pady=6)

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=16, pady=10)
        tk.Button(btns, text="Сохранить", bg="#72f700", command=self.save).pack(side=LEFT, expand=True, fill="x", padx=2)
        tk.Button(btns, text="Отмена", command=self.destroy).pack(side=LEFT, expand=True, fill="x", padx=2)

    def load_refs(self) -> None:
        con = db()
        st = con.execute("SELECT state_id, title FROM order_states ORDER BY state_id").fetchall()
        loc = con.execute("SELECT location_id, address FROM pickup_locations ORDER BY location_id").fetchall()
        items = con.execute("SELECT item_id, sku, item_name, base_price, qty FROM stock_items ORDER BY item_name").fetchall()
        con.close()

        self.state_map = {r["title"]: r["state_id"] for r in st}
        self.location_map = {r["address"]: r["location_id"] for r in loc}
        self.item_map = {
            f"{r['item_name']} ({r['sku']}) - {r['base_price']:.2f} [в наличии {r['qty']}]": (r["item_id"], r["sku"], r["item_name"], r["base_price"], r["qty"])
            for r in items
        }
        self.state_combo["values"] = list(self.state_map.keys())
        self.location_combo["values"] = list(self.location_map.keys())
        self.item_combo["values"] = list(self.item_map.keys())
        if self.state_combo["values"]:
            self.state_combo.current(0)
        if self.location_combo["values"]:
            self.location_combo.current(0)
        if self.item_combo["values"]:
            self.item_combo.current(0)

    def load_order(self, order_id: int) -> None:
        con = db()
        head = con.execute(
            """
            SELECT so.*, st.title state_title, pl.address loc
            FROM sales_orders so
            JOIN order_states st ON st.state_id=so.state_id
            JOIN pickup_locations pl ON pl.location_id=so.location_id
            WHERE so.order_id=?
            """,
            (order_id,),
        ).fetchone()
        rows = con.execute(
            """
            SELECT sor.item_id, si.sku, si.item_name, sor.qty, sor.unit_price
            FROM sales_order_rows sor
            JOIN stock_items si ON si.item_id=sor.item_id
            WHERE sor.order_id=?
            """,
            (order_id,),
        ).fetchall()
        con.close()
        if not head:
            return
        self.code.set(head["order_code"])
        self.customer.set(head["customer_name"])
        self.state.set(head["state_title"])
        self.location.set(head["loc"])
        self.created.set(head["created_on"])
        self.issued.set(head["issued_on"])
        self.items = [{"item_id": r["item_id"], "sku": r["sku"], "name": r["item_name"], "qty": r["qty"], "price": r["unit_price"]} for r in rows]
        self.repaint_rows()

    def add_row(self) -> None:
        pick = self.pick_item.get().strip()
        if not pick:
            return
        try:
            qty = int(self.pick_qty.get())
            if qty <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Ошибка", "Количество должно быть больше нуля")
            return
        item_id, sku, name, price, stock = self.item_map[pick]
        if qty > stock:
            messagebox.showerror("Ошибка", f"Недостаточно на складе. Доступно: {stock}")
            return
        self.items.append({"item_id": item_id, "sku": sku, "name": name, "qty": qty, "price": price})
        self.repaint_rows()

    def remove_row(self) -> None:
        sel = self.rows.selection()
        if not sel:
            return
        index = self.rows.index(sel[0])
        self.items.pop(index)
        self.repaint_rows()

    def repaint_rows(self) -> None:
        self.rows.delete(*self.rows.get_children())
        total = 0.0
        for idx, r in enumerate(self.items):
            cost = r["qty"] * r["price"]
            total += cost
            self.rows.insert("", END, values=(r["sku"], r["name"], r["qty"], f"{cost:.2f}"), tags=(("even" if idx % 2 == 0 else "odd"),))
        self.total_lbl.configure(text=f"Итого: {total:.2f}")

    def save(self) -> None:
        try:
            code = self.code.get().strip()
            customer = self.customer.get().strip()
            state_id = self.state_map[self.state.get().strip()]
            location_id = self.location_map[self.location.get().strip()]
            created = self.created.get().strip()
            issued = self.issued.get().strip()

            if not code or not customer:
                raise ValueError("Код заказа и клиент обязательны")
            dt.date.fromisoformat(created)
            dt.date.fromisoformat(issued)

            con = db()
            if self.order_id is None:
                cur = con.execute(
                    "INSERT INTO sales_orders(order_code, customer_name, state_id, location_id, created_on, issued_on) VALUES (?, ?, ?, ?, ?, ?)",
                    (code, customer, state_id, location_id, created, issued),
                )
                oid = cur.lastrowid
            else:
                con.execute(
                    "UPDATE sales_orders SET order_code=?, customer_name=?, state_id=?, location_id=?, created_on=?, issued_on=? WHERE order_id=?",
                    (code, customer, state_id, location_id, created, issued, self.order_id),
                )
                oid = self.order_id
                con.execute("DELETE FROM sales_order_rows WHERE order_id=?", (oid,))

            for r in self.items:
                con.execute(
                    "INSERT INTO sales_order_rows(order_id, item_id, qty, unit_price) VALUES (?, ?, ?, ?)",
                    (oid, r["item_id"], r["qty"], r["price"]),
                )
            con.commit()
            con.close()
            self.parent.refresh()
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Код заказа должен быть уникальным")
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))


def main() -> None:
    setup_database()
    app = UrbanGearApp()
    app.mainloop()


if __name__ == "__main__":
    main()
