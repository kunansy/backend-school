from dataclasses import dataclass
from datetime import time, datetime
from typing import List, Iterable, Dict, Optional, Tuple

import asyncpg
from environs import Env
from sanic.log import logger, error_logger

from src.db_commands import COMMANDS, TABLES


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
TIME_FORMAT = "%H:%M"
PATCHABLE_FIELDS = [
    'courier_type', 'regions', 'working_hours'
]
DEFAULT_COURIER_TYPES = [
    {"type": 'foot', 'c': 2, 'payload': 10},
    {"type": 'bike', 'c': 5, 'payload': 15},
    {"type": 'car', 'c': 9, 'payload': 50},
]


def is_json_patching_courier_valid(json_dict: dict) -> List[str]:
    """
    Check whether the request to patch a courier valid

    :return: list of invalid fields if there are.
    """
    json_dict = json_dict.copy()
    for field in PATCHABLE_FIELDS:
        json_dict.pop(field, None)

    return list(json_dict.keys())


env = Env()
env.read_env()


class TimeSpan:
    def __init__(self,
                 value: str) -> None:
        start, stop = value.split('-')

        self.__start = TimeSpan.parse_time(start)
        self.__stop = TimeSpan.parse_time(stop)

        if start >= stop:
            raise ValueError("Start must me be less than stop")

    @property
    def start(self) -> time:
        return self.__start

    @property
    def stop(self) -> time:
        return self.__stop

    @classmethod
    def parse_time(cls,
                   time_string: str) -> time:
        return datetime.strptime(time_string, TIME_FORMAT).time()

    def is_intercept(self, other) -> bool:
        return self | other

    def __or__(self, other) -> bool:
        if self.start <= other.start:
            return not(self.stop <= other.start)
        return not(other.stop <= self.start)

    def __repr__(self) -> str:
        return f"{self.start.strftime(TIME_FORMAT)}-" \
               f"{self.stop.strftime(TIME_FORMAT)}"

    def __eq__(self, other) -> bool:
        return self.start == other.start and \
               self.stop == other.stop


@dataclass
class _Courier:
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[TimeSpan]
    coeff: int
    payload: int

    def __init__(self,
                 courier: asyncpg.Record) -> None:
        self.courier_id = int(courier.get('courier_id'))
        self.courier_type = courier.get('type')
        self.regions = [
            int(region)
            for region in courier.get('regions')
        ]
        self.working_hours = [
            TimeSpan(time_)
            for time_ in courier.get('working_hours')
        ]
        self.coeff = int(courier.get('c'))
        self.payload = int(courier.get('payload'))

    def dict(self) -> dict:
        return self.__dict__

    def json_dict(self) -> dict:
        working_hours = [
            str(span)
            for span in self.working_hours
        ]
        return {
            "courier_id": self.courier_id,
            "courier_type": self.courier_type,
            "regions": self.regions,
            "working_hours": working_hours,
            "c": self.coeff,
            "payload": self.payload
        }

    def external(self) -> dict:
        working_hours = [
            str(h)
            for h in self.working_hours
        ]
        return {
            "courier_id": self.courier_id,
            "courier_type": self.courier_type,
            "regions": self.regions,
            "working_hours": working_hours
        }

    def is_order_valid(self, order) -> bool:
        is_time_intercept = False
        for w_time in self.working_hours:
            for d_time in order.delivery_hours:
                if w_time | d_time:
                    is_time_intercept = True
                    break

        return (
            order.weight <= self.payload and
            order.region in self.regions and
            is_time_intercept
        )


@dataclass
class _Order:
    order_id: int
    weight: float
    region: int
    delivery_hours: List[TimeSpan]

    def __init__(self,
                 order: asyncpg.Record) -> None:
        self.order_id = int(order.get('order_id'))
        self.weight = float(order.get('weight'))
        self.region = int(order.get('region'))
        self.delivery_hours = [
            TimeSpan(time_)
            for time_ in order.get('delivery_hours')
        ]


@dataclass
class _Status:
    id: int
    courier_id: int
    order_id: int
    assigned_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None

    def __init__(self,
                 status: asyncpg.Record) -> None:
        self.id = int(status.get('id'))
        self.courier_id = int(status.get('courier_id'))
        self.order_id = int(status.get('order_id'))

        if assigned_time := status.get('assigned_time', None):
            self.assigned_time = parse_date(assigned_time)
        if completed_time := status.get('completed_time', None):
            self.completed_time = parse_date(completed_time)

    def dict(self) -> dict:
        return self.__dict__

    def json_dict(self) -> dict:
        if assigned_time := self.assigned_time:
            assigned_time = assigned_time.strftime(DATE_FORMAT)
        if completed_time := self.completed_time:
            completed_time = completed_time.strftime(DATE_FORMAT)

        return {
            "id": self.id,
            "courier_id": self.courier_id,
            "order_id": self.order_id,
            "assigned_time": assigned_time,
            "completed_time": completed_time
        }


@dataclass
class CourierStatus:
    orders: List[_Order]
    statuses: List[_Status]
    courier: _Courier

    def __init__(self,
                 data: List[asyncpg.Record],
                 courier: _Courier) -> None:
        self.orders = [
            _Order(order)
            for order in data
        ]
        self.statuses = [
            _Status(status)
            for status in data
        ]
        self.courier = courier


def now() -> str:
    return datetime.now().strftime(DATE_FORMAT)


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)


class Database:
    def __init__(self) -> None:
        self._pool = None

    async def connect(self) -> None:
        if self._pool:
            return
        logger.info("Connecting to the database")
        self._pool: asyncpg.Pool = await asyncpg.create_pool(
            dsn=env('DB_DSN'),
            command_timeout=60,
            max_size=20
        )
        logger.info("Connection pool created")

    async def close(self) -> None:
        logger.info("Closing connection to the database")
        await self._pool.close()
        logger.info("Connection pool closed")

    async def migrate(self) -> None:
        """
        Make migration: drop all databases with the same names,
        create new ones according to the schemas.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                logger.info("Migration started")
                await Database._drop_tables(TABLES, conn)
                await Database._create_tables(COMMANDS['create'], conn)
                await Database._fill_tables(conn)

    @staticmethod
    async def _drop_tables(tables: Iterable[str],
                           conn: asyncpg.Connection) -> None:
        logger.info("Dropping tables")

        for table in tables:
            await conn.execute(
                f"DROP TABLE IF EXISTS {table} CASCADE;"
            )
            logger.info("'%s' dropped", table)

    @staticmethod
    async def _create_tables(commands: Dict[str, str],
                             conn: asyncpg.Connection) -> None:
        logger.info("Create tables")

        for table, command in commands.items():
            await conn.execute(command)
            logger.info("'%s' created", table)

    @staticmethod
    async def _fill_tables(conn: asyncpg.Connection) -> None:
        logger.info("Filling courier_types table")

        values = ', '.join(
            f"('{t['type']}', {t['c']}, {t['payload']})"
            for t in DEFAULT_COURIER_TYPES
        )

        query = f"""
        INSERT INTO
            courier_types (type, c, payload)
        VALUES
            {values}
        ;
        """

        await conn.execute(query)
        logger.info("courier_types filled")

    async def _get(self,
                   query: str,
                   conn: asyncpg.Connection) -> List[asyncpg.Record]:
        try:
            logger.info("Requested to the database:\n %s", query)
            result = await conn.fetch(query)
        except Exception:
            error_logger.exception('')
            raise
        logger.info("Request successfully completed")
        return result

    async def get(self,
                  query: str) -> List[asyncpg.Record]:
        """ Fetch query without transaction """
        async with self._pool.acquire() as conn:
            return await self._get(query, conn)

    async def get_t(self,
                    query: str) -> List[asyncpg.Record]:
        """ Fetch query with transaction """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                return await self._get(query, conn)

    async def _execute(self,
                       query: str,
                       conn: asyncpg.Connection) -> str:
        try:
            logger.info("Requested to the database:\n %s", query)
            result = await conn.execute(query)
        except Exception:
            error_logger.exception('')
            raise
        logger.info("Request successfully completed")
        return result

    async def execute(self,
                      query: str) -> str:
        """ Execute the query without transaction """
        async with self._pool.acquire() as conn:
            return await self._execute(query, conn)

    async def execute_t(self,
                        query: str) -> str:
        """ Execute the query with transaction """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                return await self._execute(query, conn)

    async def add_couriers(self,
                           couriers: list) -> dict:
        if not couriers:
            return {"couriers": []}

        values = ', '.join(
            f"""(
            {courier.courier_id}::INTEGER,
            (SELECT t.id FROM courier_types t WHERE t.type = '{courier.courier_type}'),
            ARRAY{courier.regions}::INTEGER[],
            ARRAY{courier.working_hours}::VARCHAR[])
            """
            for courier in couriers
        )

        query = f"""
        INSERT INTO
            couriers
        VALUES
            {values}
        ;
        """
        logger.info("Adding %s couriers", len(couriers))
        await self.execute_t(query)
        logger.info("Couriers added")

        return {
            "couriers": [
                {"id": courier.courier_id}
                for courier in couriers
            ]
        }

    async def get_courier(self,
                          courier_id: int) -> Optional[_Courier]:
        query = f"""
        SELECT 
            c.courier_id, t.type, c.regions, 
            c.working_hours, t.c, t.payload
        FROM 
            couriers c
        INNER JOIN 
            courier_types t ON c.courier_type = t.id
        WHERE 
            c.courier_id = {courier_id}::INTEGER
        ;
        """
        logger.info("Getting courier id=%s", courier_id)
        result = await self.get(query)
        try:
            return _Courier(result[0])
        except IndexError:
            logger.info("Courier not found")
            return

    async def _get_uncompleted_orders(self,
                                      courier_id: int) -> [_Order]:
        """ Get all assigned but uncompleted orders """
        get_uncompleted_orders_ids = f"""
        SELECT 
            order_id 
        FROM 
            status 
        WHERE 
            courier_id = {courier_id} AND 
            completed_time IS NULL AND 
            assigned_time IS NOT NULL
        ;
        """
        logger.info("Getting uncompleted orders")
        uncompleted_orders_ids = await self.get(get_uncompleted_orders_ids)

        if not uncompleted_orders_ids:
            logger.debug("Uncompleted orders not found")
            return []

        logger.info("Found %s uncompleted orders", len(uncompleted_orders_ids))

        uncompleted_orders_ids = ', '.join(
            str(record.get('order_id'))
            for record in uncompleted_orders_ids
        )

        uncompleted_orders_condition = f"order_id IN ({uncompleted_orders_ids})"
        return await self.get_orders(uncompleted_orders_condition)

    async def _get_free_orders(self) -> List[_Order]:
        query = f"""
        SELECT
            o.*
        FROM 
            status s
        RIGHT JOIN
            orders o
        ON
            s.order_id = o.order_id
        WHERE
            s.order_id IS NULL
        ;
        """
        logger.info("Getting free orders")
        free_orders = await self.get(query)
        logger.info("%s free orders found", len(free_orders))

        return [
            _Order(order)
            for order in free_orders
        ]

    async def cancel_orders(self,
                            orders_to_cancel: List[_Order]) -> None:
        if not orders_to_cancel:
            return
        logger.info("Cancelling %s orders", len(orders_to_cancel))

        orders_ids = ', '.join(
            f"{order.order_id}"
            for order in orders_to_cancel
        )
        query = f"""
        DELETE FROM 
            status
        WHERE 
            order_id IN ({orders_ids})
        ;
        """
        await self.execute_t(query)
        logger.debug("Orders cancelled")

    async def update_courier(self,
                             **data) -> _Courier:
        courier_id = data.pop('courier_id')

        values, is_first = "", True
        for field, value in data.items():
            if not is_first:
                values += ', '

            if field in ['regions', 'working_hours']:
                type_ = 'INTEGER' if field == 'regions' else 'VARCHAR'
                values += f"{field} = ARRAY{value}::{type_}[]"
            elif field == 'courier_type':
                values += f"""
                courier_type = 
                    (SELECT t.id FROM courier_types t WHERE t.type = '{value}')
                """

            is_first = False

        update_query = f"""
        UPDATE 
            couriers 
        SET 
            {values}
        WHERE 
            courier_id = {courier_id}::INTEGER
        RETURNING
            courier_id, 
            (SELECT t.type FROM courier_types t WHERE t.id = courier_type),
            regions,
            working_hours,
            (SELECT t.c FROM courier_types t WHERE t.id = courier_type),
            (SELECT t.payload FROM courier_types t WHERE t.id = courier_type)
        ;
        """
        logger.info("Updating courier id=%s", courier_id)
        updated_courier = await self.get_t(update_query)
        logger.info("Courier updated")

        courier = _Courier(updated_courier[0])
        uncompleted_orders = await self._get_uncompleted_orders(courier_id)

        orders_to_cancel = [
            order
            for order in uncompleted_orders
            if not courier.is_order_valid(order)
        ]
        await self.cancel_orders(orders_to_cancel)

        return courier

    async def get_orders(self,
                         condition: str) -> List[_Order]:
        query = f"""
        SELECT 
            *
        FROM
            orders
        WHERE
            {condition}
        ;
        """
        logger.info("Getting orders by %s", condition)
        orders = await self.get(query)
        logger.info("Found %s orders", len(orders))

        return [
            _Order(order)
            for order in orders
        ]

    async def add_orders(self,
                         orders: list) -> dict:
        if not orders:
            return {"orders": []}

        values = ', '.join(
            f"""(
            {order.order_id}::INTEGER,
            {order.weight}::REAL,
            {order.region}::INTEGER,
            ARRAY{order.delivery_hours}::VARCHAR[]
            )"""
            for order in orders
        )

        query = f"""
        INSERT INTO
            orders
        VALUES
            {values}
        ;
        """
        logger.info("Adding %s orders", len(orders))
        await self.execute_t(query)
        logger.info("Orders added")

        return {
            "orders": [
                {"id": order.order_id}
                for order in orders
            ]
        }

    async def assign_orders(self,
                            courier_id: int) -> Tuple[List[_Order], str]:
        # TODO: add delivery_id to the status table
        #  and to _Status, make it autoincrement
        courier = await self.get_courier(courier_id)
        free_orders = await self._get_free_orders()

        if not (free_orders and courier):
            return [], ''

        valid_orders = [
            order
            for order in free_orders
            if courier.is_order_valid(order)
        ]

        if not valid_orders:
            return [], ''

        now_ = now()

        values = ', '.join(
            f"""(
            {courier_id}::INTEGER,
            {order.order_id}::INTEGER,
            '{now_}'::VARCHAR)
            """
            for order in valid_orders
        )

        query = f"""
        INSERT INTO
            status (courier_id, order_id, assigned_time)
        VALUES
            {values}
        ;
        """

        logger.info("Assigning %s orders to Courier id=%s",
                    len(valid_orders), courier_id)
        await self.execute_t(query)
        logger.info("Orders assigned")

        return valid_orders, now_

    async def courier_status(self,
                             courier_id: int) -> Optional[CourierStatus]:
        orders_and_statuses = await self._status(courier_id=courier_id)
        if not orders_and_statuses:
            return

        courier = await self.get_courier(courier_id)

        return CourierStatus(orders_and_statuses, courier)

    async def order_status(self,
                           order_id: int) -> Optional[CourierStatus]:
        orders_and_statuses = await self._status(order_id=order_id)
        if not orders_and_statuses:
            return

        courier_id = int(orders_and_statuses[0].get('courier_id'))
        courier = await self.get_courier(courier_id)

        return CourierStatus(orders_and_statuses, courier)

    async def _status(self,
                      *,
                      order_id: int = None,
                      courier_id: int = None) -> Optional[List[asyncpg.Record]]:
        if not (order_id or courier_id):
            return

        if courier_id:
            courier_id = f"s.courier_id = {courier_id}::INTEGER"
        if order_id:
            order_id = f"s.order_id = {order_id}::INTEGER"

        if courier_id and order_id:
            condition = f"{courier_id} AND {order_id}"
        else:
            condition = courier_id or order_id

        query = f"""
        SELECT
            o.order_id, o.weight, 
            o.region, o.delivery_hours,
            s.id, s.courier_id, s.order_id,
            s.assigned_time, s.completed_time
        FROM
            status s
        INNER JOIN
            orders o
        ON
            s.order_id = o.order_id
        WHERE
            {condition}
        ;
        """
        logger.info("Getting Courier info with his orders")
        return await self.get(query)

    async def complete_order(self,
                             order_id: int,
                             completed_time: str) -> None:
        logger.info("Completing order id=%s, time=%s",
                    order_id, completed_time)
        query = f"""
        UPDATE 
            status
        SET
            completed_time = '{completed_time}'::VARCHAR
        WHERE
            order_id = {order_id}::INTEGER
        ;
        """
        await self.execute_t(query)
        logger.info("Order completed")
