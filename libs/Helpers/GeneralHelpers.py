import cProfile
import pstats
import numpy as np
import asyncio
import websockets
import cv2
import time
import os
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

DEFAULT_FRAME_WIDTH = 256
DEFAULT_FRAME_HEIGHT = 240
SURROGATE_RANGE_SIZE = 2048
OFFSET = 16

class SpeedProfiler:
    def __init__(self):
        self.pr = cProfile.Profile()

    def start(self):
        self.pr.enable()

    def stop(self, num_results=20):
        self.pr.disable()
        stats = pstats.Stats(self.pr)
        #stats.sort_stats(pstats.SortKey.TIME)
        stats.sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats(num_results)


def load_json_file(file_path):
    file_path = os.path.abspath(file_path)
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def save_json_file(data, file_path):
    file_path = os.path.abspath(file_path)
    folder_path = os.path.dirname(file_path)
    os.makedirs(folder_path, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, separators=(',', ': '))