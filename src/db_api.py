def get_courier_types() -> list[str]:
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
