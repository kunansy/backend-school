__all__ = 'COMMANDS',

CREATE_COURIER_TABLE = """
CREATE TABLE courier(
    courier_id SERIAL PRIMARY KEY,
    courier_type REFERENCES courier_type (id),
    regions INTEGER[],
    working_hours VARCHAR[] 
);
"""

CREATE_COURIER_TYPE_TABLE = """
CREATE TABLE courier_type(
    id SERIAL PRIMARY KEY,
    type VARCHAR(5) NOT NULL,
    c INTEGER NOT NULL,
    payload INTEGER NOT NULL
);
"""

CREATE_ORDER_TABLE = """
CREATE TABLE order(
    order_id SERIAL PRIMARY KEY,
    weight REAL NOT NULL,
    region INTEGER NOT NULL,
    delivery_hours VARCHAR[] NOT NULL
);
"""

CREATE_STATUS_TABLE = """
CREATE TABLE status(
    id SERIAL PRIMARY KEY,
    courier_id REFERENCES courier (courier_id),
    order_id REFERENCES order (order_id),
    assigned_time TIME DEFAULT NOW()::TIME,
    completed_time DEFAULT NULL
);
"""

COMMANDS = {
    "create": {
        "courier": CREATE_COURIER_TABLE,
        "courier_type": CREATE_COURIER_TYPE_TABLE,
        "order": CREATE_ORDER_TABLE,
        "status": CREATE_STATUS_TABLE
    },
    "get": {
        "courier": "SELECT {fields} FROM courier",
        "courier_type": "SELECT {fields} FROM courier_type",
        "order": "SELECT {fields} FROM order",
        "status": "SELECT {fields} FROM status"
    },
    "insert": {
        "courier": "INSERT INTO courier VALUES {values}",
        "order": "INSERT INTO order VALUES {values}",
        "order_type": "INSERT INTO courier_type VALUES {values}",
    },
    "update": {
        "UPDATE courier SET {fields} WHERE {condition}"
    },
    "delete": {}
}
