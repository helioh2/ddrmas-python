


import asyncio
import random


cache = dict()

async def query(x, y):

    if (x, y) in cache.keys():
        print("ESPERANDO FUTURE...")
        return await cache[(x, y)]

    loop = asyncio.get_running_loop()

    # Create a new Future object.
    fut = loop.create_future()

    cache[(x,y)] = fut


    ##...

    ans = str(x+y) + " " + str(random.random())

    cache[(x, y)].set_result(ans)

    return ans



async def main():
    res1 = await query(10, 20)
    print(res1)
    await asyncio.sleep(3)
    res2 = await query(10, 20)
    print(res2)


asyncio.run(main())
