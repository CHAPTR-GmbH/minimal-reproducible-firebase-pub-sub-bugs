import logging
from enum import Enum

from firebase_functions import firestore_fn

logger = logging.getLogger(__name__)


class FN_EVENT_TYPE(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


def get_fn_event_type(
    event: firestore_fn.Event[firestore_fn.DocumentSnapshot],
) -> FN_EVENT_TYPE:
    before = event.data.before
    after = event.data.after

    if before and after:
        return FN_EVENT_TYPE.UPDATE

    if not before and after:
        return FN_EVENT_TYPE.CREATE

    if before and not after:
        return FN_EVENT_TYPE.DELETE

    raise ValueError("get_event_type Unknown event type")


