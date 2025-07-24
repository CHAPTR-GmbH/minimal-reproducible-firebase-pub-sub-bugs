import logging
import os
from typing import Optional

from firebase_functions import https_fn
from google.cloud import logging_v2


def get_execution_id_from_request(request: https_fn.Request) -> Optional[str]:
    """
    Extract execution_id from different types of Firebase function request objects.

    Args:
        request: Can be https_fn.Request

    Returns:
        execution_id string if found, None otherwise
    """

    # For HTTPS functions (https_fn.Request)
    if hasattr(request, "headers") and hasattr(request.headers, "get"):
        return request.headers.get("Function-Execution-Id")

    return None


def setup_logging(
    name: str | None = "",
    request: https_fn.Request = None,
    disable_logging_client: bool = False,
) -> None:
    """
    Set up logging with optional execution_id for tracing.

    Args:
        name: Logger name
        request: Request object associated with the function execution
    """

    if (
        os.environ.get("CI") == "true"
        or os.environ.get("DISABLE_LOGGING_CLIENT") == "true"
        or disable_logging_client
    ):
        logging.basicConfig(
            level=logging.INFO, format=f"%(levelname)s:{name}: %(message)s"
        )

        logger = logging.getLogger()
        # Remove all CloudLoggingHandler instances
        for handler in logger.handlers[:]:
            # print("HANDLER: ", handler, handler.__class__.__name__)
            if handler.__class__.__name__ == "CloudLoggingHandler":
                logger.removeHandler(handler)

        return

    # Configure labels for the logging handler if execution_id is provided
    execution_id = get_execution_id_from_request(request) if request else None
    labels = {"execution_id": execution_id} if execution_id else None

    client = logging_v2.Client()
    client.setup_logging(labels=labels)


def log_attempt_number(retry_state):
    """return the result of the last tenacity retry attempt"""
    print(f"Retrying: {retry_state.attempt_number}...")
