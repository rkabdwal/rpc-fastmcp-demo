# rpc_client.py
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        resp = await client.call_tool(
            "nl_query",
            {"request": "List the top 5 products by list price"}
        )
        for row in resp:
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
