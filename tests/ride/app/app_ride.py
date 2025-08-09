from grpcAPI.app import GrpcAPI
from tests.ride.userdriver.drivers import module_drivers
from tests.ride.userdriver.users import module_users

app = GrpcAPI()

app.add_service(module_drivers)
app.add_service(module_users)
