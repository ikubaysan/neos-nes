import asyncio
import websockets
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

HOST = '10.0.0.147'
PORT = 9002

async def send_message(websocket, message):
    await websocket.send(message)
    #print(f"Sent message: {message}")

async def handle_connection(websocket, path):
    while True:
        # Send a string with 3 UTF-32 characters
        message = '\U0001F600\U0001F601\U0001F602'
        await send_message(websocket, message)
        logger.info(f"Sent UTF-32 message: {message} (Bytes: {len(message.encode('utf-8'))})")
        await asyncio.sleep(1)

        #message = '\U0010FFFF\U00110000\U00110001'
        message = r'\U0010FFFF\U00110000\U00110001'
        await send_message(websocket, message)
        logger.info(f"Sent UTF-32 message beyond codepoint limit: {message} (Bytes: {len(message.encode('utf-8'))})")
        await asyncio.sleep(1)

        # Send a string with 3 ASCII characters
        await send_message(websocket, 'abc')
        logger.info(f"Sent ASCII message: abc (Bytes: {len('abc'.encode('utf-8'))})")
        await asyncio.sleep(1)

async def main():
    start_server = await websockets.serve(handle_connection, HOST, PORT)
    print(f"WebSocket server started at ws://{HOST}:{PORT}")
    await start_server.wait_closed()

asyncio.run(main())
