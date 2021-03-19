from src.model import CourierModel


def get_courier_types() -> list[str]:
    return ['foot', 'car', 'bike']


async def add_couriers(couriers: list[CourierModel]) -> None:
    # logger.info(f"{len(couriers)} added to database")
    pass


async def get_courier(value,
                      field: str = 'id') -> CourierModel:
    pass


async def update_courier(courier: CourierModel) -> None:
    # await assign_order(courier.courier_id)
    # logger.info(f"{courier.courier_id} updated")
    pass
