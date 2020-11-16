import trio


async def main():
    async with trio.open_nursery() as nursery:
        send_channel1, receive_channel1 = trio.open_memory_channel(0)
        send_channel2, receive_channel2 = trio.open_memory_channel(0)

        async with send_channel1, receive_channel1, \
                send_channel2, receive_channel2:
            nursery.start_soon(kick,
                               send_channel1.clone())

            nursery.start_soon(prodcons, 'A',
                               receive_channel1.clone(),
                               send_channel2.clone())
            nursery.start_soon(prodcons, 'B',
                               receive_channel2.clone(),
                               send_channel1.clone())


async def prodcons(name, receive_channel, send_channel):
    async with receive_channel, send_channel:
        async for value in receive_channel:
            if value:
                new_value = value - 1
                await send_channel.send(new_value)
                print(f'{name} has sent {new_value}')
            else:
                await send_channel.aclose()


async def kick(send_channel):
    async with send_channel:
        await send_channel.send(10)
        print('kick with 10')


trio.run(main)
