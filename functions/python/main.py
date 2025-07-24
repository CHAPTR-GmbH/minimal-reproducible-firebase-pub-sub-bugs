import logging

from firebase_functions import (
    firestore_fn,
    pubsub_fn,
    options,
)

from app.handlers.products_sync import (
    products_sync_bulk_handler,
    products_sync_handler,
)
from app.services.firebase_admin import get_admin_app
from app.logging import setup_logging

logger = logging.getLogger(__name__)



# Triggers on firestore_products_collection_name document created and updated
# Populates pubsub from firestore_products_collection_name collection
@firestore_fn.on_document_written(
    document="products" + "/{productId}",
    memory=options.MemoryOption.GB_1,
    ingress=options.IngressSetting.ALLOW_INTERNAL_ONLY,
    region="europe-west4",
    min_instances=1,
    max_instances=50,
    timeout_sec=300,
    concurrency=5,
    cpu=1,
    enforce_app_check=True,
    service_account="dummy-service-account1@dummy-project.iam.gserviceaccount.com",
)
def products_sync(
    event: firestore_fn.Event[firestore_fn.DocumentSnapshot],
) -> None:
    setup_logging(disable_logging_client=True)
    logger.info(f"products_sync triggered. event.id={event.id}")
    products_sync_handler(event)
    return True


# Triggered by pubsub subscription, pulls messages from the bulk topic and processes them
# TODO: Make sure to optimize this to not overburden the sync
# We need to make it update in bulk, but not more than x bulk messages a second
# That means we should time how long does it take for this fn to run and then adjust the max instances and concurrency accordingly
@pubsub_fn.on_message_published(
    topic="trigger-products",  # This should be config.trigger_topic_name but the damn emulator wont work with this or .value
    region="europe-west4",
    service_account="dummy-service-account2@dummy-project.iam.gserviceaccount.com",
    memory=options.MemoryOption.GB_1,
    ingress=options.IngressSetting.ALLOW_INTERNAL_ONLY,
    min_instances=1,
    max_instances=1,
    timeout_sec=300,
    concurrency=1,
    cpu=1,
)
def products_sync_bulk(
    event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData],
) -> None:
    setup_logging(disable_logging_client=True)
    logger.info(f"products_sync_bulk triggered. event.id={event.id}")
    products_sync_bulk_handler(event)
    return True



firebase_admin_app = get_admin_app()
