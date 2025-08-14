from typing_extensions import Annotated
from grpcAPI.data_types import Depends
from grpcAPI.prototypes import KeyValueStr, StringValue

from example.guber.auth import async_authentication
from example.guber.domain.models import CPF, CarPlate, EmailStr

from example.guber.packages.account import (
    account_package,
    AccountRepo,
    get_account_repo,
    Account,
    AccountInfo,
)

account_module = account_package.make_module("account")

account_services = account_module.make_service("account_services")


@account_services(request_type_input=AccountInfo)
async def signup_account(
    name: str,
    cpf: CPF,
    email: EmailStr,
    car_plate: CarPlate,
    _: Annotated[None, Depends(async_authentication, order=0)],
    acc_repo: Annotated[AccountRepo, Depends(get_account_repo)],
) -> StringValue:
    # cpf, email and car_plate are here for validation, and to define the input protobuf class
    await acc_repo.exist_cpf(cpf=cpf)
    await acc_repo.exist_email(email=email)
    user_id = await acc_repo.create_account(
        name=name, email=email, cpf=cpf, car_plate=car_plate, is_driver=bool(car_plate)
    )
    return StringValue(value=str(user_id))


@account_services(request_type_input=StringValue)
async def get_account(
    value: str,
    _: Annotated[None, Depends(async_authentication, order=0)],
    acc_repo: Annotated[AccountRepo, Depends(get_account_repo)],
) -> Account:

    account = await acc_repo.get_by_id(value)
    if account is None:
        raise ValueError(f"Account with id {value} not found")
    return account


@account_services(request_type_input=KeyValueStr)
async def update_car_plate(
    key: str,
    value: CarPlate,
    _: Annotated[None, Depends(async_authentication, order=0)],
    acc_repo: Annotated[AccountRepo, Depends(get_account_repo)],
) -> None:
    id, car_plate = key, value
    updated = await acc_repo.update_account_field(id, "car_plate", str(car_plate))
    if not updated:
        raise ValueError(f"Account with id {id} not found or car plate not updated")


@account_services(request_type_input=KeyValueStr)
async def update_email(
    key: str,
    value: EmailStr,
    _: Annotated[None, Depends(async_authentication, order=0)],
    acc_repo: Annotated[AccountRepo, Depends(get_account_repo)],
) -> None:
    id, email = key, value
    updated = await acc_repo.update_account_field(id, "email", str(email))
    if not updated:
        raise ValueError(f"Account with id {id} not found or car plate not updated")
