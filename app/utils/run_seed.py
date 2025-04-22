import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_session
from app.utils.seed_normative_data import seed_normative_data

async def main():
    async for session in get_session():
        await seed_normative_data(session)

if __name__ == "__main__":
    asyncio.run(main())