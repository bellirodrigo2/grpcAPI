from grpcAPI.app import GrpcAPI

from example.guber.account import account_package
from example.guber.ride import ride_package

app = GrpcAPI()

app.add_service(account_package)
app.add_service(ride_package)
