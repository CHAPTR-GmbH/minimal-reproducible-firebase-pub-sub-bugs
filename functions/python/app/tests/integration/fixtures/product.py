import pytest
from app.models.product import  FirestoreProduct


def create_dummy_product():
    return FirestoreProduct(
        **{
            "id": "1",
            "title": "Dummy Title",
        }
    )


@pytest.fixture
def dummy_product():
    return create_dummy_product()

