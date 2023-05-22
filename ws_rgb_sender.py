import asyncio
import websockets
import logging
import random
import struct

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

HOST = '10.0.0.147'
PORT = 9002

def rgb_to_utf32(r, g, b):
    """Takes an RGB tuple and converts it into a single UTF-32 character"""
    r >>= 2
    g >>= 2
    b >>= 2
    rgb_int = r<<10 | g<<5 | b
    # Adjust if in the Unicode surrogate range
    if 0xD800 <= rgb_int <= 0xDFFF:
        logger.info("Avoiding Unicode surrogate range")
        if rgb_int < 0xDC00:
            rgb_int = 0xD7FF  # Maximum value just before the surrogate range
        else:
            rgb_int = 0xE000  # Minimum value just after the surrogate range
    logger.info(f"RGB int: {rgb_int}")
    return chr(rgb_int)

def utf32_to_rgb(utf32_str):
    """Converts a UTF-32 string to an RGB tuple"""
    rgb_int = ord(utf32_str)
    r = (rgb_int>>10 & 0x3F) << 2
    g = (rgb_int>>5 & 0x3F) << 2
    b = (rgb_int & 0x3F) << 2
    return (r, g, b)

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
        message = rgb_to_utf32(r, g, b)

        longer_message = "prefix_" + message + "_suffix"
        await send_message(websocket, longer_message)
        logger.info(f"Sent random RGB message: {longer_message} (Bytes: {len(longer_message.encode('utf-32'))})")

        # Decode the message back into RGB values and log them
        r_decoded, g_decoded, b_decoded = utf32_to_rgb(message)
        logger.info(f"Decoded RGB values: ({r_decoded}, {g_decoded}, {b_decoded})")

        await asyncio.sleep(1)

async def main():
    start_server = await websockets.serve(handle_connection, HOST, PORT)
    logger.info(f"WebSocket server started at ws://{HOST}:{PORT}")
    await start_server.wait_closed()

asyncio.run(main())