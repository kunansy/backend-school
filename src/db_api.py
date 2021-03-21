from typing import List


def get_courier_types() -> List[str]:
    return ['foot', 'car', 'bike']


async def add_couriers(couriers: list) -> None:
    # logger.info(f"{len(couriers)} added to database")
    pass


async def get_courier(value,
                      field: str = 'courier_id'):
    pass


async def update_courier(courier) -> None:
    # await assign_order(courier.courier_id)
    # logger.info(f"{courier.courier_id} updated")
    pass


async def get_order(value,
                    field: str = 'order_id'):
    pass


async def add_orders(order: list) -> None:
    pass


async def assign_orders(courier_id: int) -> list:
    pass


async def assign_info(order_id: int):
    pass


async def complete_order(complete) -> None:
    pass