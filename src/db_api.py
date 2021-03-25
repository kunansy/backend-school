from dataclasses import dataclass
from datetime import time, datetime
from typing import List, Callable, Iterable, Dict, Optional

import asyncpg
from environs import Env
from sanic.log import logger, error_logger

from src.db_commands import COMMANDS, TABLES


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

env = Env()
env.read_env()


class TimeSpan:
    TIME_FORMAT = "%H:%M"

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
        return datetime.strptime(time_string, cls.TIME_FORMAT).time()

    def is_intercept(self, other) -> bool:
        return self | other

    def __or__(self, other) -> bool:
        if self.start <= other.start:
            return not(self.stop <= other.start)
        return not(other.stop <= self.start)

    def __repr__(self) -> str:
        return f"{self.start.strftime(self.TIME_FORMAT)}-" \
               f"{self.stop.strftime(self.TIME_FORMAT)}"

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
        return {
            field: str(value)
            for field, value in self.dict().items()
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
        is_time_intercept = any(
            w_time | d_time
            for w_time, d_time in zip(self.working_hours, order.delivery_hours)
        )
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
        self.id = status.get('id')
        self.courier_id = status.get('courier_id')
        self.order_id = status.get('order_id')

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
           completed_time =  completed_time.strftime(DATE_FORMAT)

        return {
            "id": str(self.id),
            "courier_id": str(self.courier_id),
            "order_id": str(self.order_id),
            "assigned_time": assigned_time,
            "completed_time": completed_time
        }


@dataclass
class OrderStatus:
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


def async_cache(func: Callable) -> Callable:
    results = []

    async def wrapped(*args, **kwargs) -> List[str]:
        nonlocal results
        results = results or await func(*args, **kwargs)

        return results

    return wrapped


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

        self._pool: asyncpg.Pool = await asyncpg.create_pool(
            dsn=env('DB_DSN'),
            command_timeout=60,
            max_size=20
        )
        logger.debug("Connection pool created")

    async def close(self) -> None:
        await self._pool.close()
        logger.debug("connection pool closed")

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
        logger.debug("Dropping tables...")

        for table in tables:
            await conn.execute(
                f"DROP TABLE IF EXISTS {table} CASCADE;"
            )
            logger.info(f"'{table}' dropped")

    @staticmethod
    async def _create_tables(commands: Dict[str, str],
                             conn: asyncpg.Connection) -> None:
        logger.debug("Create tables...")

        for table, command in commands.items():
            await conn.execute(command)
            logger.info(f"'{table}' created")

    @staticmethod
    async def _fill_tables(conn: asyncpg.Connection) -> None:
        logger.debug("Filling courier_types table")

        query = f"""
        INSERT INTO
            courier_types (type, c, payload)
        VALUES
            ('foot', 2, 10), 
            ('bike', 5, 15), 
            ('car', 9, 50)
        ;
        """

        await conn.execute(query)
        logger.info("Courier_types filled")

    async def _get(self,
                   query: str,
                   conn: asyncpg.Connection) -> List[asyncpg.Record]:
        try:
            logger.debug(f"Requested to the database:\n{query}")
            result = await conn.fetch(query)
        except Exception:
            error_logger.exception('')
            raise
        logger.debug("Request successfully completed")
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
            logger.debug(f"Requested to the database:\n{query}")
            result = await conn.execute(query)
        except Exception:
            error_logger.exception('')
            raise
        logger.debug("Request successfully completed")
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

    @async_cache
    async def get_courier_types(self) -> List[str]:
        query = f"""
        SELECT 
            type
        FROM 
            courier_types
        ;
        """
        records = await self.get(query)

        return [
            record.get('type')
            for record in records
        ]

    async def add_couriers(self,
                           couriers: list) -> None:
        if not couriers:
            return

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
        logger.debug(f"Adding {len(couriers)} couriers")
        await self.execute_t(query)
        logger.debug("Couriers added")

    async def get_courier(self,
                          courier_id: int) -> _Courier or None:
        query = f"""
        SELECT 
            c.courier_id, t.type, c.regions, 
            c.working_hours, t.c, t.payload
        FROM 
            couriers c
        INNER JOIN 
            courier_types t ON c.courier_type = t.id
        WHERE 
            c.courier_id = {courier_id}::integer
        ;
        """
        logger.debug(f"Getting courier {courier_id=}")
        result = await self.get(query)
        try:
            return _Courier(result[0])
        except IndexError:
            logger.debug("Courier not found")
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
        logger.debug("Getting uncompleted orders")
        uncompleted_orders_ids = await self.get(get_uncompleted_orders_ids)

        if not uncompleted_orders_ids:
            logger.debug("Uncompleted orders not found")
            return []

        uncompleted_orders_ids = ', '.join(
            str(record.get('order_id'))
            for record in uncompleted_orders_ids
        )

        uncompleted_orders_condition = f"""
        WHERE 
            order_id IN ({uncompleted_orders_ids})
        """
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
        free_orders = await self.get(query)

        return [
            _Order(order)
            for order in free_orders
        ]

    async def cancel_orders(self,
                            orders_to_cancel: List[_Order]) -> None:
        if not orders_to_cancel:
            return
        logger.debug(f"Cancelling {len(orders_to_cancel)} orders")

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
                             **data):
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
            courier_id = {courier_id}::integer
        RETURNING
            courier_id, 
            (SELECT t.type FROM courier_types t WHERE t.id = courier_type),
            regions,
            working_hours,
            (SELECT t.c FROM courier_types t WHERE t.id = courier_type),
            (SELECT t.payload FROM courier_types t WHERE t.id = courier_type)
        ;
        """
        logger.debug(f"Updating courier {courier_id=}")
        updated_courier = await self.get_t(update_query)
        logger.debug(f"Courier updated")
        courier = _Courier(updated_courier[0])

        uncompleted_orders = await self._get_uncompleted_orders(courier_id)

        orders_to_cancel = [
            order
            for order in uncompleted_orders
            if not courier.is_order_valid(order)
        ]

        await self.cancel_orders(orders_to_cancel)

        return updated_courier

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
        orders = await self.get(query)

        return [
            _Order(order)
            for order in orders
        ]

    async def add_orders(self,
                         orders: list) -> None:
        orders = ', '.join(
            f"""(
            {order.order_id}::integer,
            {order.weight}::real,
            {order.region}::integer,
            ARRAY{order.delivery_hours}::varchar[]
            )"""
            for order in orders
        )

        query = f"""
        INSERT INTO
            orders
        VALUES
            {orders}
        ;
        """
        await self.execute_t(query)

    async def assign_orders(self,
                            courier_id: int) -> List[_Order]:
        courier = await self.get_courier(courier_id)
        free_orders = await self._get_free_orders()

        if not free_orders:
            return []

        valid_orders = [
            order
            for order in free_orders
            if courier.is_order_valid(order)
        ]

        if not valid_orders:
            return []

        now_ = now()

        values = ', '.join(
            f"""(
            {courier_id}::INTEGER,
            {order.order_id}::INTEGER,
            {now_}::VARCHAR)
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

        await self.execute_t(query)

        return valid_orders

    async def courier_status(self,
                             courier_id: int) -> Optional[OrderStatus]:
        orders_and_statuses = await self._status(courier_id=courier_id)
        if not orders_and_statuses:
            return

        courier = await self.get_courier(courier_id)

        return OrderStatus(orders_and_statuses, courier)

    async def order_status(self,
                           order_id: int) -> Optional[OrderStatus]:
        orders_and_statuses = await self._status(order_id=order_id)
        if not orders_and_statuses:
            return

        courier_id = int(orders_and_statuses[0].get('courier_id'))
        courier = await self.get_courier(courier_id)

        return OrderStatus(orders_and_statuses, courier)

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
        return await self.get(query)

    async def complete_order(self,
                             complete) -> None:
        pass
