import concurrent
import asyncio
import serial_asyncio
import sys
import os

async def tcp_remote_client(port, title, loop):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888, loop=loop)

    writer.write('{}\n'.format(title).encode('utf-8'))

    class TransportNotifier(object):
        def __init__(self):
            self.transport = None

        def connection_made(self, transport):
            self.transport = transport

        def connection_lost(self):
            self.transport = None

    notifier = TransportNotifier()

    class Output(asyncio.Protocol):
        def __init__(self, writer, notifier):
            self.writer = writer
            self.notifier = notifier

        def connection_made(self, transport):
            self.transport = transport
            print('port opened', transport)
            transport.serial.rts = False
            self.notifier.connection_made(transport)

        def data_received(self, data):
            print('data received', repr(data))
            self.writer.write(data)

        def connection_lost(self, exc):
            print('port closed')
            asyncio.get_event_loop().stop()
            self.writer.write(b'Serial connection lost.')
            self.notifier.connection_lost()

    coroutine = serial_asyncio.create_serial_connection(loop,lambda: Output(writer,notifier), port, baudrate=115200)
    asyncio.ensure_future(coroutine,loop=loop)

    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            print('no more data from remote')
            break
        print('rs>',repr(data))
        if notifier.transport is not None:
            notifier.transport.write(data)

    writer.close()


if __name__ == '__main__':
    import argv 
    import sys
    if len(argv) < 3:
        print('Usage: {} <serial_port> <title>'.format(argv[0]))
        sys.exit()

    port = argv[1]
    title = argv[2]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_remote_client(port, title, loop))
    loop.close()
