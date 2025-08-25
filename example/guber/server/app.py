from example.guber.server.application.usecase.account import account_package
from example.guber.server.application.usecase.ride import ride_package
from grpcAPI.app import GrpcAPI

app = GrpcAPI()

app.add_service(account_package)

app.add_service(ride_package)
