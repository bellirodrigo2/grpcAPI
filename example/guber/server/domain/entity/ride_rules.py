from grpcAPI.prototypes import Timestamp
from example.guber.server.domain import Ride, Account,RideStatus


def accept_ride(ride:Ride, account:Account)->None:

    if not account.info.is_driver:
        raise ValueError("Account is not from a driver")
    if ride.status != RideStatus.REQUESTED:
        raise ValueError("Invalid status")
    if ride.accepted_at is not None:
        raise ValueError(f"Inconsistent Ride: Status '{ride.status}' with accepted_at '{ride.accepted_at}'")
	
    ride.driver_id = account.account_id
    ride.status = RideStatus.ACCEPTED
    ts_now = Timestamp()
    ts_now.GetCurrentTime()
    ride.accepted_at = ts_now
    