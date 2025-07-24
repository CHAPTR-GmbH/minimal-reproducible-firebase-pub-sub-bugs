import json
import time
from datetime import datetime

from app.models.product import (
    FirestoreProduct,
)


def get_another_model_from_product(data: FirestoreProduct):
    ts_data = json.loads(
        data.model_dump_json()
    )  # model_dump_json will serialize timestamps and similar fields


    return ts_data
