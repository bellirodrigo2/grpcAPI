from typing import Annotated, List

from grpcAPI.app import App, Package
from grpcAPI.proto_inject import FromContext, FromRequest
from grpcAPI.types import Context, Int32, Metadata, OneOf, Stream


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
            EMPLOYEE = 0
            SCHOOL = -247
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
            affilliation: str

        id_desc = "this is a long description that should be formatted, because it has more than 80 characteres"

        class User(UserInput):
            id: str = Metadata(description=id_desc)
            employee: Annotated[str, OneOf("occupation")]
            school: Annotated[str, OneOf("occupation")]
            inactive: Annotated[bool, OneOf("occupation")]

        class UserNames(mod1.ProtoModel):
            ids: List[int]
            employee: Annotated[str, OneOf("occupation")]

        class UserList(mod1.ProtoModel):
            users: List[User]
            index: Annotated[Int32, Metadata(index=12)]

        user_service = mod2.Service("user_service", description="User Services")

        @user_service(description="Make New User")
        async def newuser(
            request: UserInput,
            userage: str = FromRequest(model=UserInput, field="age"),
            peer: str = FromContext(),
        ) -> User:
            userproxy = User(age=userage, id="0", name=request.name)

            key = request.code.name.lower()
            if key not in ("employee", "school", "inactive"):
                raise ValueError(f"Occupation = {key}")
            affiliation = (
                request.affilliation
                if key != "inactive"
                else bool(request.affilliation)
            )
            setattr(userproxy, key, affiliation)
            print(f"Received newuser: '{userproxy}' from: '{peer}'")

            return userproxy

        @user_service(description="get a list of users")
        async def getusers(request: UserNames) -> Stream[User]:
            print(f"getusers called with ids: {request.ids}")
            for i in request.ids:
                yield User(age=30 + i, id="i", name=f"User {i}", inactive=True)

        @user_service()
        async def manynewuser(request: Stream[UserInput], ctx: Context) -> UserList:
            users = []
            print("Many Users received")
            try:
                async for req in request:
                    user_obj = await newuser(req, req.age, ctx.peer())
                    users.append(user_obj)
            except Exception as e:
                print(f"[Server] Error in manynewuser: {e}")
                raise

            return UserList(users=users, index=0)

        @user_service()
        async def bilateralnewuser(request: Stream[UserInput]) -> Stream[User]:
            async for req in request:
                print(f"Bilateral stream received: {req}")
                yield User(
                    age=req.age, id=str(req.code), name=req.name, employee="StreamInc"
                )

    return app
