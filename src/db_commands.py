__all__ = 'COMMANDS', 'TABLES'

CREATE_COURIER_TABLE = """
CREATE TABLE couriers (
    courier_id SERIAL PRIMARY KEY,
    courier_type INTEGER REFERENCES courier_types (id) NOT NULL,
    regions INTEGER[],
    working_hours VARCHAR[] 
);
"""

CREATE_COURIER_TYPE_TABLE = """
CREATE TABLE courier_types (
    id SERIAL PRIMARY KEY,
    type VARCHAR(5) NOT NULL,
    c INTEGER NOT NULL,
    payload INTEGER NOT NULL
);
"""

CREATE_ORDER_TABLE = """
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    weight REAL NOT NULL,
    region INTEGER NOT NULL,
    delivery_hours VARCHAR[] NOT NULL
);
"""

CREATE_STATUS_TABLE = """
CREATE TABLE status (
    id SERIAL PRIMARY KEY,
    courier_id INTEGER REFERENCES couriers (courier_id) NOT NULL,
    order_id INTEGER REFERENCES orders (order_id) NOT NULL,
    assigned_time VARCHAR,
    completed_time VARCHAR
);
"""

TABLES = {
    "courier",
    "courier_type",
    "orders",
    "status"
}

COMMANDS = {
    "create": {
        "courier_type": CREATE_COURIER_TYPE_TABLE,
        "courier": CREATE_COURIER_TABLE,
        "order": CREATE_ORDER_TABLE,
        "status": CREATE_STATUS_TABLE
    },
}
