import cv2
import logging
from abc import ABC, abstractmethod
from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.AdvancedDisplayStrategy import AdvancedDisplayStrategy

# Configure logging
logger = logging.getLogger(__name__)

HOST = '10.0.0.147'
PORT = 9001
SCALE_PERCENTAGE = 100

if __name__ == "__main__":
    display_strategy = AdvancedDisplayStrategy(host=HOST, port=PORT, scale_percentage=SCALE_PERCENTAGE)
    asyncio.run(display_strategy.receive_frames())