import subprocess
from pathlib import Path


def main():
    MICROSERVICE_PATH = Path(__file__).parent.resolve()
    app_path = str((MICROSERVICE_PATH / "app_run.py"))

    ACCOUNT_CONFIG = str((MICROSERVICE_PATH / "account.config.json"))
    RIDE_CONFIG = str((MICROSERVICE_PATH / "ride.config.json"))

    cmd = ["grpcapi", "run", app_path, "-s"]

    account_server = [*cmd, ACCOUNT_CONFIG]
    ride_server = [*cmd, RIDE_CONFIG]

    p1 = subprocess.Popen(account_server)
    p2 = subprocess.Popen(ride_server)

    p1.wait()
    p2.wait()


main()
