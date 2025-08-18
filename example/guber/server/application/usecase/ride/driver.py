
from example.guber.server.application.usecase.ride import ride_package

driver_module = ride_package.make_module("driver")

driver_services = driver_module.make_service("driver_ride_actions")


# Temporarily commented out due to ProtoKey dependency resolution issues
# @driver_services(request_type_input=KeyValueStr, tags=["write:ride", "read:account"])
# async def accept_ride(
#     ride_id: ProtoKey,
#     driver_id: ProtoValue,
#     _: Authenticate,
#     is_passenger: Annotated[bool, Depends(is_passenger)],
#     ride_repo: RideRepository,
# ) -> Empty:

#     if is_passenger:
#         raise ValueError("This account is not from a driver")

#     has_active_ride = await ride_repo.has_active_ride(driver_id)
#     if has_active_ride:
#         raise ValueError("This driver has an active ride")

#     ride = await ride_repo.get_by_id(ride_id)
#     if ride is None:
#         raise ValueError(f"Ride not found: Id: {ride_id}")
#     accept_ride_rules(ride, driver_id)
#     await ride_repo.update_ride(ride)

#     return Empty()
