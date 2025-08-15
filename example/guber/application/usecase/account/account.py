from typing_extensions import Annotated
from grpcAPI.prototypes import StringValue, ProtoStr

from example.guber.application.services import Authenticate
from example.guber.application.repo import AccountRepository
from example.guber.domain.vo.account import CPF, CarPlate, EmailStr

from example.guber.application.usecase.account import (
    account_package,
    Account,
    AccountInfo,
    FromAccountInfo
)
from grpcAPI.prototypes import FromValue, ProtoKey

account_module = account_package.make_module("account")

account_services = account_module.make_service("account_services")

@account_services
async def signup_account(
    account_info: AccountInfo,
    cpf: Annotated[CPF, FromAccountInfo()],
    email: Annotated[EmailStr, FromAccountInfo()],
    car_plate: Annotated[CarPlate, FromAccountInfo()],
    _: Authenticate,
    acc_repo: AccountRepository,
) -> StringValue:
    # cpf, email and car_plate are here for validation, and to define the input protobuf class
    await acc_repo.exist_cpf(cpf=str(cpf))
    await acc_repo.exist_email(email=str(email))
    user_id = await acc_repo.create_account(account_info)
    return StringValue(value=str(user_id))


@account_services
async def get_account(
    id: ProtoStr,
    _: Authenticate,
    acc_repo: AccountRepository,
) -> Account:

    account = await acc_repo.get_by_id(id)
    if account is None:
        raise ValueError(f"Account with id {id} not found")
    return account


@account_services
async def update_car_plate(
    id: ProtoKey,
    car_plate: Annotated[CarPlate, FromValue()],
    _: Authenticate,
    acc_repo: AccountRepository,
) -> None:
    updated = await acc_repo.update_account_field(id, "car_plate", str(car_plate))
    if not updated:
        raise ValueError(f"Account with id {id} not found or car plate not updated")


@account_services
async def update_email(
    key: ProtoKey,
    value: Annotated[EmailStr, FromValue()],
    _: Authenticate,
    acc_repo: AccountRepository,
) -> None:
    id, email = key, value
    updated = await acc_repo.update_account_field(id, "email", str(email))
    if not updated:
        raise ValueError(f"Account with id {id} not found or car plate not updated")
