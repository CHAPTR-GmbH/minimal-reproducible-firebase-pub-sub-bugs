from typing import Any

import pytest
from firebase_admin.firestore import firestore

from app.tests.integration.fixtures.init_app import (
    initialise_admin_app,
)

app = initialise_admin_app()


@pytest.fixture(scope="function")
def firestore_client():
    return firestore.Client(project=app.project_id)


@pytest.fixture(autouse=True, scope="function")
def clear_emulator(firestore_client) -> Any:
    """Clear Firebase Emulator after each test."""

    yield

    print("Clearing Firestore...")
    for collection in firestore_client.collections():
        for doc in collection.stream():
            try:
                doc.reference.delete()
            except Exception as e:
                print(f"Error deleting document {doc.id}: {e}")
