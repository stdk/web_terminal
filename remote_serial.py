import concurrent
import asyncio
import serial
import sys
import os

async def tcp_remote_client(port, loop):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                   loop=loop)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def read_data():
        data = port.read(1024)
        writer.write(data)

    with executor as e:
        loop.create_task(loop.run_in_executor(e,read_data))

    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            break
        print('>',repr(data))
        port.write(data)

    writer.close()


port_name = sys.argv[1] if len(sys.argv) > 1 else 'COM1'
port = serial.Serial(port_name)

loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_remote_client(port, loop))
loop.close()