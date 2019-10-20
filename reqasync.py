import asyncio
from aiohttp import ClientSession

async def fetch(url, session, payload, output):
    async with session.post(url, data=payload) as response:
        if output is not None:
            output.write(await response.text() + '\n')
        return await response.read()

async def bound_fetch(sem, url, session, payload, output):
    # Getter function with semaphore.
    async with sem:
        await fetch(url, session, payload, output)

async def run(r, r_sem, url, payload, output):
    tasks = []
    # Create instance of semaphore.
    sem = asyncio.Semaphore(r_sem)
    # Create client session that will ensure we dont open new connection per each request.
    async with ClientSession() as session:
        for i in range(r):
            # Pass semaphore and session to every request.
            task = asyncio.ensure_future(bound_fetch(sem, url, session, payload, output))
            tasks.append(task)
        responses = asyncio.gather(*tasks)
        await responses

def run_async(n_conc, n_sem, url, payload, output):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(n_conc, n_sem, url, payload, output))
    loop.run_until_complete(future)
