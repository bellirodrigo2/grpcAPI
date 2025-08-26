from example.guber.server.app import app
from example.guber.server.application.internal_access import is_passenger
from example.guber.server.microservice.is_passenger import is_passenger_client

app.dependency_overrides[is_passenger] = is_passenger_client
