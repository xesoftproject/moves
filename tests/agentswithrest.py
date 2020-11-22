import trio


async def main():
    async with trio.open_nursery() as nursery:
        a_send_channel, a_receive_channel = trio.open_memory_channel(0)
        b_send_channel, b_receive_channel = trio.open_memory_channel(0)
        async with a_send_channel, a_receive_channel, b_send_channel, b_receive_channel:
            nursery.start_soon(
                counter, 'A', a_receive_channel.clone(), b_send_channel.clone())
            nursery.start_soon(
                counter, 'B', b_receive_channel.clone(), a_send_channel.clone())
            await a_send_channel.send(9)


async def counter(name, receive_channel, send_channel):
    async with receive_channel, send_channel:
        async for value in receive_channel:
            print(f'{name} received {value}')
            if value > 0:
                await send_channel.send(value - 1)
            else:
                break

if __name__ == '__main__':
    trio.run(main)
