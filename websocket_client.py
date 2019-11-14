#!/usr/bin/env python

# WS client example

import asyncio
import websockets
import os

async def get_stdin():
    import sys
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader(loop=loop)
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader, loop=loop), sys.stdin)
    return reader

async def shutdown(loop):
    os.system('stty cooked echo')
    
    tasks = [task for task in asyncio.Task.all_tasks() if task is not
             asyncio.tasks.Task.current_task()]
    list(map(lambda task: task.cancel(), tasks))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    #print('finished awaiting cancelled tasks, results: {0}'.format(results))
    loop.stop()

class Controller(object):
    command_length_limit = 1
    mark = b'\x00'

    def __init__(self, reader):
        self.reader = reader
        self.commands = {
            self.mark: self.ctrl_null,
            b'q': self.exit,
        }
        self.buffer = None

    def add_to_buffer(self, data):
        self.buffer += data
        command = self.commands.get(self.buffer, None)
        if command is not None:
            self.buffer = None
            return command()

        if len(self.buffer) >= self.command_length_limit:
            result = self.buffer
            self.buffer = None
            return result

        return b''

    def process(self, data):
        if len(data) != 1:
            return data

        if self.buffer is None:
            if data == self.mark:
                self.buffer = b''
                return b''
        else:
            return self.add_to_buffer(data)

        return data

    def ctrl_null(self):
        return b'\x00'

    def exit(self):
        os.kill(os.getpid(), signal.SIGINT)
        return b''

async def writer(websocket, reader):
    stdin = await get_stdin()    

    controller = Controller(reader)
    while True:
        data = await stdin.read(100)
        data = controller.process(data)
        await websocket.send(data.decode('utf8', 'replace'))

async def reader(websocket):
    import sys

    os.system('stty raw -echo')

    while True:
        buf = await websocket.recv()
        sys.stdout.write(buf)
        sys.stdout.flush()

async def start(uri, loop):
    try:
        websocket = await websockets.connect(uri)
    except websockets.exceptions.InvalidHandshake as e:
        print('Cannot connect to[{}] ({})'.format(uri,e))
        os.kill(os.getpid(), signal.SIGINT)
        return

    reader_task = loop.create_task(reader(websocket))

    loop.create_task(writer(websocket, reader_task))

if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser()
    # ws://192.168.1.27:8000/ws/remote?title=dut6
    arg_parser.add_argument('-u','--uri',type=str, required=True,
                            help='Websocket console URL')
    args = arg_parser.parse_args()

    loop = asyncio.get_event_loop()

    import signal, functools
    for s in [signal.SIGINT]:
        loop.add_signal_handler(
            s,
            functools.partial(
                loop.create_task,
                shutdown(loop)
            )
        )

    loop.create_task(start(args.uri,loop))
    loop.run_forever()