import asyncio
import subprocess
import pty
import sys
import os

async def tcp_remote_client(cmd, loop):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                   loop=loop)

    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        cmd,
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True
    )

    def redirect(process):
        data = os.read(master_fd,1024)
        print('#',repr(data))
        writer.write(data)

    loop.add_reader(master_fd,redirect,process)

    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            break
        print('>',repr(data))
        os.write(master_fd,data)

    writer.close()


cmd = ' '.join(sys.argv[1:]) or '/bin/bash'
print('cmd',cmd)

loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_remote_client(cmd, loop))
loop.close()