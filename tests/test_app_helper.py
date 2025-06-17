from typing import Annotated, List

from grpcAPI.app import App, Package
from grpcAPI.types.base import Metadata, OneOf
from grpcAPI.types.method import Stream
from grpcAPI.types.types import Int32, String


def make_app() -> App:

    app = App()
    if not app.packages:

        pack1 = Package("pack1")
        pack2 = Package("pack2")

        app.add_package(pack1)
        app.add_package(pack2)

        mod1 = pack1.Module("mod1", description="Module1")
        mod2 = pack2.Module("mod2", description="Module2")

        class UserCode(mod1.ProtoEnum):
            NOTFOUND = -247
            ACTIVE = 0
            INACTIVE = 1

        class UserInput(mod1.ProtoModel):
            name: Annotated[
                str,
                Metadata(
                    description="user name", options={"deprecated": True}, index=4
                ),
            ]
            code: UserCode = Metadata(options={"json_name": "user_code"})
            age: int = Metadata(description="user´s age")

        id_desc = "this is a long description that should be formatted, because it has more than 80 characteres"

        class User(UserInput):
            id: str = Metadata(description=id_desc)

        class UserNames(mod1.ProtoModel):
            names: List[String]
            student: str = OneOf(key="occupation", description="The school´s name")
            employee: str = OneOf(
                key="occupation", description="The employer´s name", index=1
            )

        class UserList(mod1.ProtoModel):
            users: List[User]
            index: Annotated[Int32, Metadata(index=12)]

        user_service = mod2.Service("user_service", description="User Services")

        @user_service(description="Make New User")
        async def newuser(input: UserInput) -> Stream[User]:
            yield None

        @user_service(description="get a list of users")
        def getusers(input: Stream[UserNames]) -> UserList: ...

    return app
