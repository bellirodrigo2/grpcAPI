from typing import Any, Protocol


class PaymentGateway(Protocol):
    async def process_payment(self, *args: Any, **kwargs: Any) -> None:
        pass


def get_payment_gateway() -> PaymentGateway:
    pass
