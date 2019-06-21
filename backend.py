import os
import asyncio
import websockets
import subprocess
import pty
import json
from aiohttp import web
from collections import OrderedDict

async def main(request):
    return web.Response(
        body=open('main.html').read(),
        content_type='text/html'
    )

async def options(request):
    return web.Response(
        body=open('options.html').read(),
        content_type='text/html'
    )

async def ws_list(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    remote_manager = request.app['remote_manager']

    async for msg in ws:
        print('list_message[{}]'.format(msg.data))
        try:
            request = json.loads(msg.data)
        except json.JSONDecodeError:
            print('incorrect json')
            continue

        if 'action' not in request:
            print('missing request')
            continue

        action = request['action']
        if action == 'get':
            available = [{
                    'title': title,
                    'path': '/remote?title={}'.format(title),
                    'comment': remote_manager.get_comment(title)
                } for title in remote_manager.get_available()
            ]

            await ws.send_str(json.dumps({
                'available': available,
            }))
        elif action == 'set':
            if 'title' not in request:
                print('missing title in set request')
                continue

            if 'comment' not in request:
                print('missing comment in set request')
                continue

            remote_manager.set_comment(request['title'], request['comment'])

    return ws

async def ws_remote(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    remote_manager = request.app['remote_manager']

    if not 'title' in request.query:
        print('Title is not in request.query')
        await ws.close()
        return ws

    title = request.query['title']
    writer = remote_manager.new_ws_client(title, ws)

    if writer is None:
        print('Title[{}] not found'.format(title))
        await ws.close()
        return ws

    async for msg in ws:
        #print('!',repr(msg.data))
        if writer.transport.is_closing():
            break
        writer.write(msg.data.encode('utf-8'))

    print("[{}][{}] no more messages".format(title,request))
    remote_manager.remove_ws_client(title, ws)

    await ws.close()

    return ws

async def ws_pty(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    cmd = request.query['cmd']

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
        #print('#',repr(data))
        asyncio.ensure_future(ws.send_str(data.decode('utf-8', 'replace')))

    asyncio.get_event_loop().add_reader(master_fd,redirect,process)

    async for msg in ws:
        print('>',repr(msg.data))
        os.write(master_fd,bytes(msg.data,'utf-8'))

    return ws

class RemoteManager(object):
    def __init__(self):
        self.consoles = OrderedDict()
        self.comments = {}
        self.load_comments()

    def load_comments(self):
        try:
            self.comments = json.loads(open('comments','r').read())
        except (json.JSONDecodeError,IOError) as e:
            print('{}: {}'.format(e.__class__.__name__,e))

    def save_comments(self):
        open('comments','w').write(json.dumps(self.comments))

    def get_available(self):
        return [key for key in self.consoles]

    def set_comment(self, title, comment):
        self.comments[title] = comment

    def get_comment(self, title):
        return self.comments.get(title, 'none')

    def new_ws_client(self,title,ws_client):
        if title not in self.consoles:
           return None

        writer,ws_clients = self.consoles[title]
        ws_clients.append(ws_client)
        print('clients for[{}]:[{}]'.format(title,ws_clients))
        return writer

    def remove_ws_client(self, title, ws_client):
        if title not in self.consoles:
            return

        writer,ws_clients = self.consoles[title]
        try:
            ws_clients.remove(ws_client)
        except ValueError as e:
            print('remove_ws_client: could not remove ws_client for title[{}]'.format(title))
        print('clients for[{}]:[{}]'.format(title,ws_clients))

    async def new_remote(self,reader,writer):
        title = await reader.readline()
        title = title.decode('utf-8', 'replace')[:-1]

        async def safe_read(reader, size):
            try:
                return await reader.read(size)
            except (TimeoutError,ConnectionResetError) as e:
                print("safe_read[{}]:{}".format(e.__class__.__name__,e))
                print('safe_read from reader[{}] failed[{}]'.format(reader, e))
                return ''

        async def safe_send(client, data):
            if client.closed:
                return

            try:
                await client.send_str(data.decode('utf-8', 'replace'))
            except (TimeoutError,ConnectionResetError) as e:
                print("safe_send[{}]:{}".format(e.__class__.__name__,e))

        self.consoles[title] = [writer,[]]
        while True:
            data = await safe_read(reader, 1024)
            #print('!',repr(data))
            if len(data) == 0:
                print('remote[{}] has been lost'.format(title))
                break

            ws_clients = self.consoles[title][1]

            transmissions = (safe_send(client, data) for client in ws_clients)
            await asyncio.gather(*transmissions, return_exceptions=True)

        ws_clients = self.consoles[title][1]
        for ws_client in ws_clients:
            await ws_client.send_str('\r\nConnection closed')

        del self.consoles[title]


def setup_web_application(loop, remote_manager):
    ws_app = web.Application()

    ws_app['remote_manager'] = remote_manager
    ws_app.router.add_route('*','/list', ws_list)
    ws_app.router.add_route('*','/pty', ws_pty)
    ws_app.router.add_route('*','/remote', ws_remote)

    app = web.Application()
    app.add_subapp('/ws',ws_app)
    app.router.add_static('/xterm.js', 'xterm.js')
    app.router.add_static('/js', 'js')
    app.router.add_get(r'/options.html',options)
    app.router.add_get(r'/{name:\w*}',main)

    async def run_app():
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, args.bind_http_addr, args.http_port)
        await site.start()

    loop.create_task(run_app())


async def shutdown(sig, loop, remote_manager):
    print('caught {0}'.format(sig.name))
    remote_manager.save_comments()
    tasks = [task for task in asyncio.Task.all_tasks() if task is not
             asyncio.tasks.Task.current_task()]
    list(map(lambda task: task.cancel(), tasks))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print('finished awaiting cancelled tasks, results: {0}'.format(results))
    loop.stop()

def setup_event_loop(args):
    loop = asyncio.get_event_loop()

    remote_manager = RemoteManager()
    setup_web_application(loop, remote_manager)

    remote_server = asyncio.start_server(
        remote_manager.new_remote,
        args.bind_backend_addr, args.backend_port,
        loop=loop
    )
    loop.create_task(remote_server)

    import signal, functools
    for s in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(
            s,
            functools.partial(
                loop.create_task,
                shutdown(s, loop, remote_manager)
            )
        )     

    loop.run_forever()

if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-B','--bind-backend-addr',type=str, dest='bind_backend_addr',
                            default='0.0.0.0',
                            help='Address to bind backend server')
    arg_parser.add_argument('-P','--backend-port',type=int, dest='backend_port',
                            default=8888,
                            help='Backend port to accept connections from remotes')
    arg_parser.add_argument('-b','--bind-http-addr',type=str, dest='bind_http_addr',
                            default='0.0.0.0',
                            help='Address to bind HTTP server')
    arg_parser.add_argument('-p','--http-port',type=int, dest='http_port',
                            default=8000,
                            help='HTTP server port to serve clients')
    args = arg_parser.parse_args()

    setup_event_loop(args)