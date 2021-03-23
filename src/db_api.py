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
            command = COMMANDS['get']['courier_type'].format(
                fields='type'
            )

            logger.info(f"Requested to the database\n{command}")
            try:
                records = await conn.fetch(command)
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
        # logger.info(f"{len(couriers)} added to database")
        pass

    async def get_courier(self,
                          value,
                          field: str = 'courier_id'):
        pass

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
