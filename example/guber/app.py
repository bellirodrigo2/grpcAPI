from example.guber.packages.account import account_package
from example.guber.packages.ride import ride_package
from grpcAPI.app import GrpcAPI

app = GrpcAPI()

app.add_service(account_package)
app.add_service(ride_package)
