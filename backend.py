import os
import asyncio
import websockets
import subprocess
import pty
import json

from aiohttp import web

async def main(request):
    return web.Response(
        body=open('main.html').read(),
        content_type='text/html'
    )

async def ws_list(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    available = []

    response = {
        'available': available
    }

    for title in ws_app['remote_manager'].get_available():
        available.append({
            'title': title,
            'path': '/remote?title={}'.format(title)
        })

    print('response',response)
    
    ws.send_str(json.dumps(response))

    return ws

async def ws_remote(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if not 'title' in request.query:
        print('Title is not in request.query')
        await ws.close()
        return ws

    title = request.query['title']
    remote_manager = request.app['remote_manager']
    writer = remote_manager.new_ws_client(title,ws)

    async for msg in ws:
        print('!',repr(msg.data))
        if writer.transport.is_closing():
            break
        writer.write(msg.data.encode('utf-8'))

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
        print('#',repr(data))
        asyncio.ensure_future(ws.send_str(data.decode('utf-8', 'replace')))

    asyncio.get_event_loop().add_reader(master_fd,redirect,process)

    async for msg in ws:
        print('>',repr(msg.data))
        os.write(master_fd,bytes(msg.data,'utf-8'))

    return ws

class RemoteManager(object):
    def __init__(self):
        self.consoles = {}

    def get_available(self):
        return [key for key in self.consoles]

    def new_ws_client(self,title,ws_client):
        writer,ws_clients = self.consoles[title]
        ws_clients.append(ws_client)
        return writer

    async def new_remote(self,reader,writer):
        title = await reader.readline()
        title = title.decode('utf-8', 'replace')[:-1]

        self.consoles[title] = [writer,[]]
        while True:
            data = await reader.read(1024)
            print('!',repr(data))
            if len(data) == 0:
                break

            ws_clients = self.consoles[title][1]
            for ws_client in ws_clients:
                ws_client.send_str(data.decode('utf-8', 'replace'))

        ws_clients = self.consoles[title][1]
        for ws_client in ws_clients:
            ws_client.send_str('\r\nConnection closed')

        del self.consoles[title]


ws_app = web.Application()
ws_app.router.add_route('*','/list',ws_list)
ws_app.router.add_route('*','/pty',ws_pty)
ws_app.router.add_route('*','/remote',ws_remote)
ws_app['remote_manager'] = RemoteManager()

app = web.Application()
app.add_subapp('/ws',ws_app)
app.router.add_static('/xterm.js', 'xterm.js')
app.router.add_get(r'/{name:\w*}',main)

loop = asyncio.get_event_loop()
remote_server = asyncio.start_server(
    ws_app['remote_manager'].new_remote,
    '0.0.0.0', 8888,
    loop=loop
)
loop.create_task(remote_server)

web.run_app(app,host='0.0.0.0',port=8000)