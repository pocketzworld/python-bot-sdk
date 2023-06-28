from asyncio import run as arun

from highrise.webapi import WebAPI


async def main():
    a = WebAPI()
    try:
        temp = await a.get_users()
        print(temp)
    except Exception as e:
        print(e)


arun(main())
