from typing import List, Callable


def async_cache(func: Callable) -> Callable:
    results = []

    async def wrapped() -> List[str]:
        nonlocal results
        results = results or await func()

        return results

    return wrapped


class Database:
    def __init__(self) -> None:
        pass

    @async_cache
    async def get_courier_types(self) -> List[str]:
        return ['foot', 'car', 'bike']

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
