import asyncio

from db import engine


def check_database() -> None:
    connection = engine.connect()
    try:
        connection.execute("SELECT 1")
    finally:
        connection.close()


async def database_is_ready(timeout_seconds: float = 2.0) -> bool:
    loop = asyncio.get_running_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, check_database),
            timeout=timeout_seconds,
        )
        return True
    except Exception:
        return False
