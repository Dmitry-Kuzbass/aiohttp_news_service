import asyncio
import json
import os
from aiohttp import web

websockets = set()

async def index_handler(request):
    current_dir = os.path.dirname(__file__)
    html_path = os.path.join(current_dir, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return web.Response(text=f.read(), content_type='text/html')

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    websockets.add(ws)
    print(f"[WS] Клиент подключился. Всего в сети: {len(websockets)}")
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data.get('type') == 'ping':
                    await ws.send_json({'type': 'pong'})
    finally:
        websockets.remove(ws)
        print(f"[WS] Клиент отключился. Всего в сети: {len(websockets)}")
    return ws

async def post_news_handler(request):
    try:
        data = await request.json()
        news_text = data.get('text')
        if not news_text:
            return web.json_response({'error': 'Missing text'}, status=400)
        print(f"[POST] Получена новость: {news_text}")
        if websockets:
            payload = {'type': 'news', 'text': news_text}
            await asyncio.gather(*[ws.send_json(payload) for ws in websockets], return_exceptions=True)
        return web.json_response({'status': 'success', 'sent_to': len(websockets)})
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)

def main():
    app = web.Application()
    app.add_routes([
        web.get('/', index_handler),
        web.get('/ws', websocket_handler),
        web.post('/news', post_news_handler),
    ])
    print("Сервер запущен на http://localhost:8080")
    web.run_app(app, host='localhost', port=8080)

if __name__ == '__main__':
    main()
