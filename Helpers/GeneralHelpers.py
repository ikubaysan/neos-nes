import cProfile
import pstats
import numpy as np
import asyncio
import websockets
import cv2
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

DEFAULT_FRAME_WIDTH = 240
DEFAULT_FRAME_HEIGHT = 256

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
