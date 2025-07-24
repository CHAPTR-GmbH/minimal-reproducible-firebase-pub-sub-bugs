from typing import Any, Optional
from pydantic import BaseModel


FIRESTORE_PRODUCTS_COLLECTION_NAME = "products"


class FirestoreProduct(BaseModel):
    id: str
    title: str
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None

