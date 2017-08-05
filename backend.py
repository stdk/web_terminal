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

    response = {
        'available': [
            {
                'path':'/pty?cmd=bash',
                'title': 'bash',
            },
            {
                'path':'/pty?cmd=ping',
                'title': 'ping'
            }
        ],
    }
    
    ws.send_str(json.dumps(response))

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
        asyncio.ensure_future(ws.send_str(data.decode('utf-8')))

    asyncio.get_event_loop().add_reader(master_fd,redirect,process)

    async for msg in ws:
        print('>',repr(msg.data))
        os.write(master_fd,bytes(msg.data,'utf-8'))

    return ws

ws_app = web.Application()
ws_app.router.add_route('*','/list',ws_list)
ws_app.router.add_route('*','/pty',ws_pty)

app = web.Application()
app.add_subapp('/ws',ws_app)
app.router.add_static('/xterm.js', 'xterm.js')
app.router.add_get('/',main)


web.run_app(app,host='0.0.0.0',port=8000)