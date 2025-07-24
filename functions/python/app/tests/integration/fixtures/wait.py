import time
import pytest
from typing import Any


def wait_until_condition(condition, timeout=10, interval=0.1) -> Any:
    start_time = time.time()
    while True:
        if condition():
            return
        if time.time() - start_time > timeout:
            pytest.fail("Condition not met within timeout period")
        time.sleep(interval)


@pytest.fixture
def wait_until():
    """Wait until a condition is met."""

    return wait_until_condition
