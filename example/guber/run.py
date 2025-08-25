import asyncio

from grpcAPI.commands.run import RunCommand

from .server.app_sqlalchemy import app


async def main():
    run = RunCommand(app)
    await run.run()


if __name__ == "__main__":
    asyncio.run(main())
