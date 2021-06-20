class EOFError(Exception):
    pass

class AsyncConnectionBase:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def send(self, command):
        line = command + '\n'
        data = line.encode()
        self.writer.write(data)
        await self.writer.drain()

    async def received(self):
        line = await self.reader.readline()
        if not line:
            raise EOFError('Connection closed')
        return line[:-1].decode()
    
class AsyncSession(AsyncConnectionBase):
    def __init__(self, *args):
        super().__init__(*args)
        self._clear_state(None, None)

    def _clear_state(self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.secret = None
        self.guesses = []

    async def loop(self):
        while command := await self.receive():
            match command.split():
                case ['PARAM', lower, upper]:
                    self.set_params(int(lower), int(upper))
                case ['NUMBER', *_]:
                    self.send_number()
                case ['REPORT', decision]:
                    self.receive_report(decision)
                case _:
                    raise UnknowCommandError(command)

    def set_params(self, lower, upper):
        self._clear_state(lower, upper)

    def next_guess(self):
        if self.secret is not None:
            return self.secret

        while True:
            guess = random.randint(self.lower, self.upper)
            if guess not in self.guesses:
                return guess

    async def send_number(self):
        guess = self.next_guess()
        self.guesses.append(guess)
        await self.send(format(guess))


    def receive_report(self, decision):
        last = self.guesses[-1]
        if decision == CORRECT:
            self.secret = last

        print(f'Server: {last} is {decision}')

import contextlib
import math

class AsyncClient(AsyncConnectionBase):
    def __init__(self, *args):
        super().__init__(*args)
        self._clear_state()

    def _clear_state(self):
        self.secret = None
        self.last_distance = None

    @contextlib.asynccontextmanager
    async def session(self, lower, upper, secret):
        print(f'Guess a number between {lower} and {upper}!'
              f'Shhhhhh, it is {secret}.')
        self.secret = secret
        await self.send(f'PARAM {lower} {upper}')
        try:
            yield
        finally:
            self._clear_state()
            await self.send('PARAM 0 -1')

    async def request_numbers(self, count):
        for _ in range(count):
            await self.send('NUMBER')
            data = await self.receive()
            yield int(data)
            if self.last_distance == 0:
                return

    async def report_outcome(self, number):
        new_distance = math.fabs(number - self.secret)
        decision = UNSURE

        if new_distance == 0:
            decision = CORRECT
        elif self.last_distance is None:
            pass
        elif new_distance < self.last_distance:
            decision = WARMER
        elif new_distance > self.last_distance:
            decision = COLDER

        self.last_distance = new_distance

        await self.send(f'REPORT {decision}')
        return decision

import asyncio

async def handle_async_connection(reader, writer):
    session = AsyncSession(reader, writer)
    try:
        await session.loop()
    except EOFError:
        pass

async def run_async_server(address):
    server = await asyncio.start_server(handle_async_connection, *address)
    async with server:
        await server.serve_forever()

async def run_async_client(address):
    streams = await asyncio.open_connection(*address)
    client = AsyncClient(*streams)

    async with client.session(1, 5, 3):
        results = [(x, await client.report_outcome(x))
                    async for x in client.request_numbers(5)]

    async with client.session(10, 15, 12):
        async for number in client.request_numbers(5):
            outcome = await client.report_outcome(number)
            results.append((number, outcome))

    _, writer = streams
    writer.close()
    await writer.wait_closed()

    return results

async def main_async():
    address = ('127.0.0.1', 4321)

    server = run_async_server(address)
    asyncio.create_task(server)

    results = await run_async_client(address)
    for number, outcome in results:
        print(f'Client: {number} is {outcome}')


asyncio.run(main_async())
