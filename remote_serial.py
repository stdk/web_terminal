import asyncio
import serial_asyncio

async def tcp_remote_client(device, title, loop,
                            backend_hostname, backend_port, serial_args):

    reader, writer = await asyncio.open_connection(backend_hostname, backend_port, loop=loop)

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
            print('device[{}]: opened'.format(device), transport)
            transport.serial.rts = False
            self.notifier.connection_made(transport)

        def data_received(self, data):
            #print('data received', repr(data))
            self.writer.write(data)

        def connection_lost(self, exc):
            print('device[{}]: closed'.format(device))
            asyncio.get_event_loop().stop()
            self.writer.write(b'Serial connection lost.')
            self.notifier.connection_lost()

    coroutine = serial_asyncio.create_serial_connection(
        loop,
        lambda: Output(writer,notifier),
        device,
        **serial_args,
    )
    asyncio.ensure_future(coroutine,loop=loop)

    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            print('device[{}]: no more data from remote[{}:{}]'.format(
                device, backend_hostname, backend_port
            ))
            break
        #print('rs>',repr(data))
        if notifier.transport is not None:
            notifier.transport.write(data)

    writer.close()

async def shutdown(sig, loop):
    print('caught {0}'.format(sig.name))
    tasks = [task for task in asyncio.Task.all_tasks() if task is not
             asyncio.tasks.Task.current_task()]
    list(map(lambda task: task.cancel(), tasks))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print('finished awaiting cancelled tasks, results: {0}'.format(results))
    loop.stop()

if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-D','--device',type=str,
                            help='Serial device')
    arg_parser.add_argument('-B','--baudrate',type=int, default=115200,
                            help='Serial device baudrate')
    arg_parser.add_argument('-t','--title',type=str,
                            help='Remote title')
    arg_parser.add_argument('-b','--backend-hostname',type=str,
                            dest='backend_hostname', default='127.0.0.1',
                            help='Backend hostname')
    arg_parser.add_argument('-p','--backend-port',type=int,
                            dest='backend_port', default=8888,
                            help='Backend hostname')
    args = arg_parser.parse_args()

    loop = asyncio.get_event_loop()

    import signal, functools
    for s in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(
            s,
            functools.partial(
                loop.create_task,
                shutdown(s, loop)
            )
        )

    loop.create_task(tcp_remote_client(
        device=args.device,
        title=args.title,
        loop=loop,
        backend_hostname=args.backend_hostname,
        backend_port=args.backend_port,
        serial_args={
            'baudrate':args.baudrate,
            'rtscts':False,
        },
    ))

    loop.run_forever()