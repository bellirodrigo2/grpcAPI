from typing_extensions import Annotated, Any, Callable, Optional

from example.guber.server.application.repo import AccountRepository
from example.guber.server.domain import Account, AccountInfo, FromValue, ProtoKey
from example.guber.server.domain.entity.account_rules import make_account_id
from example.guber.server.domain.vo.account import (
    EmailStr,
    validate_car_plate,
    validate_sin,
)
from grpcAPI import APIPackage, Depends, FromRequest
from grpcAPI.protobuf import BoolValue, String, StringValue

account_package = APIPackage("account")


class FromAccountInfo(FromRequest):
    def __init__(
        self,
        field: Optional[str] = None,
        validator: Optional[Callable[..., Any]] = None,
        **meta: Any,
    ):
        super().__init__(AccountInfo, field, validator, **meta)


account_services = account_package.make_service("account_services")


@account_services(tags=["write:account"])
async def signup_account(
    account_info: AccountInfo,
    sin: Annotated[str, FromAccountInfo(validator=validate_sin)],
    email: Annotated[EmailStr, FromAccountInfo()],
    _: Annotated[str, FromAccountInfo(field="car_plate", validator=validate_car_plate)],
    id: Annotated[str, Depends(make_account_id)],
    acc_repo: AccountRepository,
) -> StringValue:
    # sin, email and car_plate are here for validation, and to define the input protobuf class
    duplicated_sin = await acc_repo.exist_sin(sin=str(sin))
    if duplicated_sin:
        raise ValueError(f"SIN {sin} is already taken")
    duplicated_email = await acc_repo.exist_email(email=str(email))
    if duplicated_email:
        raise ValueError(f"Email {email} is already taken")
    user_id = await acc_repo.create_account(id, account_info)
    return StringValue(value=user_id)


@account_services(tags=["read:account"])
async def get_account(
    id: String,
    acc_repo: AccountRepository,
) -> Account:

    account = await acc_repo.get_by_id(id)
    if account is None:
        raise ValueError(f"Account with id {id} not found")
    return account


@account_services
async def update_car_plate(
    id: ProtoKey,
    car_plate: Annotated[str, FromValue(validator=validate_car_plate)],
    acc_repo: AccountRepository,
) -> BoolValue:
    updated = await acc_repo.update_account_field(id, "car_plate", str(car_plate))
    if not updated:
        raise ValueError(f"Account with id {id} not found or car plate not updated")
    return BoolValue(value=True)


@account_services
async def update_email(
    id: ProtoKey,
    email: Annotated[EmailStr, FromValue()],
    acc_repo: AccountRepository,
) -> BoolValue:
    updated = await acc_repo.update_account_field(id, "email", str(email))
    if not updated:
        raise ValueError(f"Account with id {id} not found or email not updated")
    return BoolValue(value=True)


@account_services(tags=["read:account", "read:gateway", "internal"])
async def is_passenger(
    id: String,
    acc_repo: AccountRepository,
) -> BoolValue:
    account = await acc_repo.get_by_id(id)
    if account is None:
        raise ValueError(f"Account with id {id} not found")
    return BoolValue(value=not account.info.is_driver)
