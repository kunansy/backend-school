from dataclasses import dataclass
from datetime import time, datetime
from typing import List, Callable, Iterable, Dict

import asyncpg
from environs import Env
from sanic.log import logger, error_logger

from src.db_commands import COMMANDS, TABLES


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
        self.courier_type = courier.get('courier_type')
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


@dataclass
class _Order:
    order_id: int
    weight: float
    region: int
    delivery_hours: List[str]


def async_cache(func: Callable) -> Callable:
    results = []

    async def wrapped(*args, **kwargs) -> List[str]:
        nonlocal results
        results = results or await func(*args, **kwargs)

        return results

    return wrapped


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

    async def close(self):
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

    @staticmethod
    async def _drop_tables(tables: Iterable[str],
                           conn: asyncpg.Connection) -> None:
        logger.debug("Dropping tables...")

        for table in tables:
            await conn.execute(
                f"DROP TABLE {table};"
            )
            logger.info(f"'{table}' dropped")

    @staticmethod
    async def _create_tables(commands: Dict[str, str],
                             conn: asyncpg.Connection) -> None:
        logger.debug("Create tables...")

        for table, command in commands.items():
            await conn.execute(command)
            logger.info(f"'{table}' created")

    async def _get(self,
                   query: str,
                   conn: asyncpg.Connection):
        try:
            result = await conn.fetch(query)
        except Exception:
            error_logger.exception()
            raise
        return result

    async def get(self,
                  query: str):
        """ Perform request without transaction """
        async with self._pool.acquire() as conn:
            return await self._get(query, conn)

    async def get_t(self,
                    query: str):
        """ Perform request with transaction """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                return await self._get(query, conn)

    async def _execute(self,
                       query: str,
                       conn: asyncpg.Connection):
        try:
            result = await conn.execute(query)
        except Exception:
            error_logger.exception()
            raise
        return result

    async def execute(self,
                      query: str):
        """ Execute the query without transaction """
        async with self._pool.acquire() as conn:
            return await self._execute(query, conn)

    async def execute_t(self,
                        query: str):
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
        logger.info(f"Requested to the database:\n{query}")
        records = await self.get(query)
        logger.debug("Request successfully completed")

        return [
            record.get('type')
            for record in records
        ]

    async def add_couriers(self,
                           couriers: list) -> None:
        if not couriers:
            return

        couriers = ', '.join(
            f"({courier.courier_id}, "
            f"(SELECT t.id FROM courier_type t WHERE t.type = {courier.courier_type}), "
            f"'{{{', '.join(courier.regions)}}}', "
            f"'{{{', '.join(courier.working_hours)}}}'"
            ")"
            for courier in couriers
        )

        query = f"""
        INSERT INTO
            couriers
        VALUES
            {couriers}
        ;
        """
        logger.debug(f"Requested to the database: \n {query}")
        await self.execute_t(query)
        logger.debug(f"Couriers ({len(couriers)}) added to database")

    async def get_courier(self,
                          value,
                          field: str = 'courier_id') -> List[_Courier]:
        query = f"""
        SELECT 
            c.courier_id, t.type, c.regions, 
            c.working_hours, t.c, t.payload
        FROM 
            courier c
        INNER JOIN 
            courier_type t ON c.courier_type = t.id;
        WHERE 
            c.{field} = {value}
        ;
        """

        logger.debug(f"Requested to the database:\n{query}")
        result = await self.get(query)
        logger.debug("Request successfully compelted")

        return [
            _Courier(courier)
            for courier in result
        ]

    async def update_courier(self,
                             courier) -> None:
        # await assign_order(courier.courier_id)
        # logger.info(f"{courier.courier_id} updated")
        pass

    async def get_order(self,
                        value=None,
                        field: str = 'order_id'):
        async with self._pool.acquire() as conn:
            query = COMMANDS['get']['order'].format(
                fields='*'
            )
            if value:
                query = f"{query} WHERE {field} = {value}"

            logger.debug(f"Requested to the database: \n{query}")

            try:
                orders = await conn.fetch(query)
            except Exception:
                error_logger.exception()
                raise
            logger.debug("Request successfully completed")

            return orders

    async def add_orders(self,
                         orders: list) -> None:
        orders = ', '.join(
            f"({order.order_id}, "
            f"{order.weight}, "
            f"{order.region}, "
            f"{order.delivery_hours}"
            f")"
            for order in orders
        )

        query = f"""
        INSERT INTO
            orders
        VALUES
            {orders}
        ;
        """
        logger.debug(f"Requested to the database: \n {query}")
        await self.execute_t(query)
        logger.debug(f"Orders ({len(orders)}) added to database")

    async def assign_orders(self,
                            courier_id: int) -> list:
        pass

    async def assign_info(self,
                          order_id: int):
        pass

    async def complete_order(self,
                             complete) -> None:
        pass
