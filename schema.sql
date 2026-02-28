PRAGMA foreign_keys = ON;

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
