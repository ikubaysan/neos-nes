import numpy as np
import ctypes
from libs.CtypesLibs.CPPFrameToString import FrameToString
import pytest

@pytest.fixture
def frame_to_string():
    return FrameToString()

def test_random_frame_to_string(frame_to_string):
    current_state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)
    last_state = np.random.randint(0, 256, (240, 256, 3), dtype=np.uint8)

    result = frame_to_string.get_string(current_state, last_state)
    assert isinstance(result, str)
    assert result != ''
    print(result)