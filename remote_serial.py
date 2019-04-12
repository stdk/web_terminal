import asyncio
import serial
import serial_asyncio

class Writer(object):
    def __init__(self,device,loop):
        self.device = device
        self.loop = loop
        self.transport = None
        self.reset()

    def connection_made(self, transport):
        print('device[{}]: connection made [{}]'.format(self.device,transport))
        self.transport = transport

    def connection_lost(self):
        print('device[{}]: connection lost'.format(self.device))
        self.transport = None
        self._lost.set_result(True)

    def write(self, *args, **kwargs):
        if self.transport is not None:
            return self.transport.write(*args,**kwargs)

    def lost(self):
        return self._lost

    def reset(self):
        self._lost = asyncio.Future(loop=self.loop)

class Protocol(asyncio.Protocol):
    def __init__(self, backend_writer, device_writer):
        self.backend_writer = backend_writer
        self.device_writer = device_writer

    def connection_made(self, transport):
        self.backend_writer.write(b'\r\nSerial connection established.\r\n')
        self.device_writer.connection_made(transport)

    def data_received(self, data):
        #print('data received', repr(data))
        self.backend_writer.write(data)

    def connection_lost(self, exc):
        self.backend_writer.write(b'\r\nSerial connection lost.\r\n')
        self.device_writer.connection_lost()


async def connect_to_backend(host, port, title, loop):
    reader,writer = await asyncio.open_connection(host,port,loop=loop)
    writer.write('{}\n'.format(title).encode('utf-8'))

    return reader,writer


async def device_watcher(args, device_writer, backend_writer, loop):
    while True:
        print('connection to serial device[{}]'.format(args.device))
        coroutine = serial_asyncio.create_serial_connection(
            loop,
            lambda: Protocol(backend_writer, device_writer),
            args.device,
            baudrate=args.baudrate,
            rtscts=False
        )

        try:
            await coroutine
        except serial.serialutil.SerialException:
            print('file not found')
            await asyncio.sleep(2)
            continue

        print('waiting for lost connection')
        await device_writer.lost()
        print('connection has been lost')
        device_writer.reset()
        await asyncio.sleep(2)
        

async def server(args,loop):
    backend_writer = Writer('backend',loop)
    device_writer = Writer(args.device,loop)

    loop.create_task(device_watcher(args, device_writer, backend_writer, loop))    

    while True:
        print('Connecting to backend...')
        try:
            reader,writer = await connect_to_backend(
                args.backend_hostname,
                args.backend_port,
                args.title,
                loop
            )
        except Exception as e:
            print(e.__class__.__name__,e)
            await asyncio.sleep(5)
            continue

        backend_writer.connection_made(writer)

        while True:
            data = await reader.read(1024)
            if len(data) == 0:
                print('device[{}]: no more data from remote[{}:{}]'.format(
                    device, backend_hostname, backend_port
                ))
                break

            device_writer.write(data)

        backend_writer.connection_lost()

        reader.close()
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

    loop.create_task(server(args,loop))

    loop.run_forever()