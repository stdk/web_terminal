import asyncio
import subprocess
import pty
import sys
import os

async def connect_to_backend(host, port, title, loop):
    reader,writer = await asyncio.open_connection(host,port,loop=loop)
    writer.write('{}\n'.format(title).encode('utf-8'))

    return reader,writer

async def endpoint(args, loop):
    reader, writer = await connect_to_backend(args.backend_hostname,
                                              args.backend_port,
                                              args.title,
                                              loop=loop)

    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        args.command.split(),
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True
    )

    def redirect(process):
        data = os.read(master_fd,1024)
        #print('#',repr(data))
        writer.write(data)

    loop.add_reader(master_fd,redirect,process)

    while True:
        data = await reader.read(1024)
        if len(data) == 0:
            break
        #print('>',repr(data))
        os.write(master_fd,data)

    writer.close()


async def tcp_remote_client(args, loop):
    while True:
        try:
             await endpoint(args, loop)
        except (ConnectionRefusedError,ConnectionResetError,TimeoutError) as e:
             print(e.__class__.__name__,e)
        await asyncio.sleep(10)


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
    arg_parser.add_argument('-t','--title',type=str,
                            help='Remote title')
    arg_parser.add_argument('-b','--backend-hostname',type=str,
                            dest='backend_hostname', default='127.0.0.1',
                            help='Backend hostname')
    arg_parser.add_argument('-p','--backend-port',type=int,
                            dest='backend_port', default=9999,
                            help='Backend port')
    arg_parser.add_argument('-c','--command',type=str,
                            dest='command', default="/bin/bash",
                            help='Command to run')
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

    loop.create_task(tcp_remote_client(args, loop))

    loop.run_forever()

