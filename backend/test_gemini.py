import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from app.services.llm_service import generate_response
from app.db.session import AsyncSessionLocal

async def main():
    try:
        resp = await generate_response('hello', 'hello', 1.0, [], [])
        print('SUCCESS:', resp)
    except Exception as e:
        print('ERROR:', e)

asyncio.run(main())
