import asyncio
import websockets
import zlib
import cv2
import numpy as np
import imageio

HOST = 'localhost'
PORT = 9001

async def receive_frames():
    uri = f"ws://{HOST}:{PORT}"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    png_data = await websocket.recv()
                    frame = imageio.imread(png_data)
                    cv2.imshow('NES Emulator Frame Viewer', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        except Exception as e:
            print(f"Error: {e}")
            print("Trying to reconnect in 5 seconds...")
            await asyncio.sleep(5)
    cv2.destroyAllWindows()


asyncio.run(receive_frames())
