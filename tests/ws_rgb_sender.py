import asyncio
import websockets
import logging
import random

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

async def handle_connection(websocket, path):
    while True:
        # Generate random RGB values divisible by 4
        r = random.choice(range(0, 256, 4))
        g = random.choice(range(0, 256, 4))
        b = random.choice(range(0, 256, 4))

        logger.info("")
        logger.info(f"Chosen RGB: {r}, {g}, {b}")

        # Convert RGB values to Unicode format
        message = rgb_to_utf8(r, g, b)

        longer_message = "prefix_" + message + "_suffix"
        await send_message(websocket, longer_message)
        # Encoding as UTF-8, but in Logix we will decode the RGB character as UTF-8.
        # This still works because the unicode code points are identical for both.
        logger.info(f"Sent random RGB message: {longer_message} (Bytes: {len(longer_message.encode('utf-8'))})")

        # Decode the message back into RGB values and log them
        r_decoded, g_decoded, b_decoded = utf8_to_rgb(message)
        logger.info(f"Decoded RGB values: ({r_decoded}, {g_decoded}, {b_decoded})")

        await asyncio.sleep(1)

async def main():
    start_server = await websockets.serve(handle_connection, HOST, PORT)
    logger.info(f"WebSocket server started at ws://{HOST}:{PORT}")
    await start_server.wait_closed()

asyncio.run(main())