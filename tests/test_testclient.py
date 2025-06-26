import unittest
from typing import Any, Generator, List

from grpcAPI.testclient import TestClient
from tests.test_app_helper import (
    UserCode,
    UserInput,
    UserNames,
    bilateralnewuser,
    getusers,
    make_app,
    manynewuser,
    newuser,
)

app = make_app()
client = TestClient(app)


class TestValidateFunc(unittest.IsolatedAsyncioTestCase):

    async def test_unary(self) -> None:
        code = UserCode.EMPLOYEE
        name = "John"
        age = 60
        affilliation = "google"
        user_input = UserInput(name=name, code=code, age=age, affilliation=affilliation)

        user = await client.run(newuser, user_input)

        self.assertEqual(user.name, name)
        self.assertEqual(user.id, "0")
        self.assertEqual(user.WhichOneof("occupation"), "employee")
        self.assertEqual(user.employee, affilliation)
        self.assertEqual(user.school, "")
        self.assertEqual(user.inactive, False)

    async def test_client_stream(self) -> None:
        user_inputs = [
            UserInput(
                code=UserCode.EMPLOYEE,
                age=28,
                name="Alice",
                affilliation="ACME Corp",
            ),
            UserInput(
                code=UserCode.SCHOOL,
                age=22,
                name="Bob",
                affilliation="UniX University",
            ),
            UserInput(code=UserCode.INACTIVE, age=45, name="Charlie", affilliation=""),
        ]

        response = await client.run(manynewuser, user_inputs)

        for u in response.users:
            occ = u.WhichOneof("occupation")
            val = getattr(u, occ)

            self.assertEqual(u.id, "0")
            self.assertIn(u.name, ["Alice", "Bob", "Charlie"])
            self.assertIn(u.age, [22, 28, 45])
            self.assertEqual(getattr(u, occ), val)

    async def test_server_stream(self) -> None:
        names = UserNames(ids=[1, 2, 3, 4])
        response_iterator = await client.run(getusers, names)

        age = 31
        async for user in response_iterator:
            self.assertEqual(user.id, "i")
            self.assertTrue(user.name.startswith("User"))
            int(user.name[-1])
            self.assertEqual(user.age, age)
            age += 1
            self.assertTrue(user.inactive)

    async def test_bilateral_stream(self) -> None:

        def generate_requests() -> Generator[UserInput, Any, None]:
            users: List[UserInput] = [
                UserInput(
                    code=UserCode.EMPLOYEE,
                    age=35,
                    name="Diana",
                    affilliation="Globex",
                ),
                UserInput(
                    code=UserCode.SCHOOL,
                    age=20,
                    name="Evan",
                    affilliation="Springfield College",
                ),
                UserInput(
                    code=UserCode.INACTIVE,
                    age=50,
                    name="Frank",
                    affilliation="",
                ),
            ]
            for user in users:
                yield user

        responses = await client.run(bilateralnewuser, generate_requests())

        async for resp in responses:
            occ = resp.WhichOneof("occupation")
            val = getattr(resp, occ)

            self.assertIn(resp.id, ["0", "-247", "1"])
            self.assertIn(resp.name, ["Diana", "Evan", "Frank"])
            self.assertIn(resp.age, [20, 35, 50])
            self.assertEqual(getattr(resp, occ), val)
