from google.cloud import firestore
from app.models.product import (
    FirestoreProduct,
    FIRESTORE_PRODUCTS_COLLECTION_NAME,
)

PRODUCT_404 = "Product with id=%s is not found in Firestore collection=%s."

def get_product_ref_by_id(product_id: str) -> firestore.DocumentReference:
    firestore_client = firestore.Client()
    return firestore_client.collection(FIRESTORE_PRODUCTS_COLLECTION_NAME).document(
        product_id
    )


def get_product_by_id(product_id: str, collection_name: str = FIRESTORE_PRODUCTS_COLLECTION_NAME) -> FirestoreProduct:
    product_ref = get_product_ref_by_id(product_id)
    product = product_ref.get()

    if not product.exists:
        raise ValueError(PRODUCT_404 % (product_id, collection_name))

    product = FirestoreProduct(**product.to_dict())

    return product


def update_product_by_id(product_id, updates: dict[str, any], collection_name: str = FIRESTORE_PRODUCTS_COLLECTION_NAME) -> dict[str, any]:
    firestore_client = firestore.Client()

    product_update_data = (
        firestore_client.collection(collection_name)
        .document(product_id)
        .update(updates)
    )

    return product_update_data


def upsert_product_by_id(product_id, data: dict[str, any], collection_name: str = FIRESTORE_PRODUCTS_COLLECTION_NAME) -> dict[str, any]:
    firestore_client = firestore.Client()

    product_update_data = (
        firestore_client.collection(collection_name)
        .document(product_id)
        .set(data)
    )

    return product_update_data


def delete_product_by_id(id: str, collection_name: str = FIRESTORE_PRODUCTS_COLLECTION_NAME):
    firestore_client = firestore.Client()
    firestore_client.collection(collection_name).document(
        id
    ).delete()
