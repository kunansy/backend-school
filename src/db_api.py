from typing import List, Callable, Iterable, Dict

import asyncpg
from environs import Env
from sanic.log import logger, error_logger

from src.db_commands import COMMANDS, TABLES


env = Env()
env.read_env()


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
        async with self._pool.acquire() as conn:
            query = COMMANDS['get']['courier_type'].format(
                fields='type'
            )

            logger.info(f"Requested to the database:\n{query}")
            try:
                records = await conn.fetch(query)
            except Exception as e:
                error_logger.exception(e)
                raise
            logger.debug("Request successfully completed")

            return [
                record.get('type')
                for record in records
            ]

    async def add_couriers(self,
                           couriers: list) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                query = COMMANDS['insert']['courier']
                couriers = ', '.join(
                    f"({courier.courier_id}, "
                    f"(SELECT t.id FROM courier_type t WHERE t.type = {courier.courier_type}),"
                    f"'{{{', '.join(courier.regions)}}}',"
                    f"'{{{', '.join(courier.working_hours)}}}'"
                    ")"
                    for courier in couriers
                )
                query = f"{query} {couriers};"
                logger.debug(f"Requested to the database: \n {query}")

                try:
                    await conn.execute(query)
                except Exception:
                    error_logger.exception()
                    raise

            logger.debug(f"Couriers ({len(couriers)}) added to database")

    async def get_courier(self,
                          value,
                          field: str = 'courier_id'):
        async with self._pool.acquire() as conn:
            query = f"""
            SELECT 
                c.courier_id, t.type, c.regions, c.working_hours,
                t.c, t.payload
            FROM 
                courier c
            INNER JOIN 
                courier_type t ON c.courier_type = t.id;
            WHERE 
                c.{field} = {value}
            ;
            """

            logger.debug(f"Requested to the database:\n{query}")
            try:
                result = await conn.fetch(query)
            except Exception:
                logger.exception()
                raise
            logger.debug("Request successfully compelted")

            return result

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
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                query = COMMANDS['insert']['order']
                orders = ', '.join(
                    f"({order.order_id}, "
                    f"{order.weight}, "
                    f"{order.region}, "
                    f"{order.delivery_hours}"
                    ")"
                    for order in orders
                )
                query = f"{query} {orders};"
                logger.debug(f"Requested to the database: \n {query}")

                try:
                    await conn.execute(query)
                except Exception:
                    error_logger.exception()
                    raise

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
