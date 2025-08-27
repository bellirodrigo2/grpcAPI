from typing import Any

from example.guber.server.adapters.repo.sqlalchemy import (
    get_account_sqlalchemy_repo,
    init_db,
)
from example.guber.server.adapters.repo.sqlalchemy.position_repo import (
    get_position_sqlalchemy_repo,
)
from example.guber.server.adapters.repo.sqlalchemy.ride_repo import (
    get_ride_sqlalchemy_repo,
)
from example.guber.server.application.gateway.payment import (
    PaymentGateway,
    get_payment_gateway,
)
from example.guber.server.application.repo import get_account_repo
from example.guber.server.application.repo.position_repo import get_position_repo
from example.guber.server.application.repo.ride_repo import get_ride_repo
from example.guber.server.application.usecase.account import account_package
from example.guber.server.application.usecase.ride import ride_package
from example.guber.server.loginterceptor import LoggingInterceptor
from grpcAPI.app import GrpcAPI

app = GrpcAPI()

app.add_service(account_package)
app.add_service(ride_package)
app.add_interceptor(LoggingInterceptor())

app.dependency_overrides[get_account_repo] = get_account_sqlalchemy_repo
app.dependency_overrides[get_ride_repo] = get_ride_sqlalchemy_repo
app.dependency_overrides[get_position_repo] = get_position_sqlalchemy_repo


class MockPaymentGateway(PaymentGateway):
    async def process_payment(self, *args: Any, **kwargs: Any) -> None:
        print(f"Paying: {kwargs}")


def mock_payment_gateway() -> PaymentGateway:
    return MockPaymentGateway()


app.dependency_overrides[get_payment_gateway] = mock_payment_gateway

app.lifespan.append(init_db)
