import trio

from moves.autils import ctxms, open_memory_channel_tee


async def main():
    async with trio.open_nursery() as nursery:
        input_send, input_receive = trio.open_memory_channel(0)
        output_send, output_receive1, output_receive2 = open_memory_channel_tee(
            0)
        async with ctxms(input_send, input_receive,
                         output_send, output_receive1, output_receive2):
            nursery.start_soon(game_engine,
                               input_receive.clone(),
                               output_send.clone())

            nursery.start_soon(rest, input_send.clone())
            nursery.start_soon(amq_client, output_receive1.clone())

            nursery.start_soon(cpu,
                               input_send.clone(),
                               output_receive2.clone())


async def game_engine(input_receive, output_send):
    async with ctxms(input_receive, output_send):
        async for value in input_receive:
            outvalue = value.upper()
            await trio.sleep(.3)
            print(f'[{"game_engine": <11}] received {value}, sending {outvalue}')
            await output_send.send(outvalue)


async def rest(input_send):
    async with input_send:
        print(f'[{"rest": <11}] ')
        await input_send.send('ping')


async def amq_client(output_receive):
    async with output_receive:
        async for value in output_receive:
            print(f'[{"amq_client": <11}] received {value}')


COUNTER = 0


async def cpu(input_send, output_receive):
    async with input_send, output_receive:
        async for value in output_receive:
            outvalue = 'ping' if value == 'PONG' else 'pong'

            global COUNTER
            if COUNTER < 5:
                COUNTER += 1
                await trio.sleep(.2)
                print(f'[{"cpu": <11}] received {value}, sending {outvalue}')

                await input_send.send(outvalue)
            else:
                print(f'[{"cpu": <11}] the game should stop')
                await input_send.aclose()

trio.run(main)
