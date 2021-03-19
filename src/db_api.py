from src.model import CourierModel


def get_courier_types() -> list[str]:
    return ['foot', 'car', 'bike']


async def add_couriers(couriers: list[CourierModel]) -> None:
    # logger.info(f"{len(couriers)} added to database")
    pass