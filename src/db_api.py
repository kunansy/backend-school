from typing import List, Callable

import asyncpg
from environs import Env
from sanic.log import logger, error_logger

from src.db_commands import COMMANDS


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
            query = COMMANDS['insert']['courier']
            couriers = ', '.join(
                f"({courier.courier_id}, "
                f"(SELECT t.id FROM courier_type t WHERE t.type = {courier.courier_type}),"
                f"{courier.regions},"
                f"{courier.working_hours}"
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
                        value,
                        field: str = 'order_id'):
        pass

    async def add_orders(self,
                         order: list) -> None:
        pass

    async def assign_orders(self,
                            courier_id: int) -> list:
        pass

    async def assign_info(self,
                          order_id: int):
        pass

    async def complete_order(self,
                             complete) -> None:
        pass
