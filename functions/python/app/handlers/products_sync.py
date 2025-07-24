import logging
import json
import time

from firebase_functions.firestore_fn import (
    Event,
    DocumentSnapshot,
)
from google.cloud import pubsub_v1
from google.api_core.exceptions import DeadlineExceeded
from pydantic import BaseModel
from app.models.product import (
    FirestoreProduct,
)
from app.services.firestore import get_fn_event_type, FN_EVENT_TYPE
from app.services.product.firestore import delete_product_by_id, get_product_by_id, upsert_product_by_id
from app.services.product import get_another_model_from_product
from app.services.pubsub import (
    get_or_create_subscription,
    get_or_create_topic,
    get_pubsub_publisher_client,
    get_pubsub_subscriber_client,
)

_logger = logging.getLogger(__name__)


class TriggerMessage(BaseModel):
    product_id: str
    event_type: FN_EVENT_TYPE


BULK_TOPIC_NAME="bulk-products"
TRIGGER_TOPIC_NAME="trigger-products"

###################################################################################
############################# FIRESTORE HANDLER ###################################
###################################################################################
# This is the main function that is called when a product is updated in firestore.
# It will create a message to be processed by the bulk function.
# It will also trigger the bulk function to be called.
###################################################################################


def get_product_from_event(
    event: Event[DocumentSnapshot], event_type: FN_EVENT_TYPE
) -> FirestoreProduct:
    # GET PRODUCT DATA FROM EVENT
    if event_type == FN_EVENT_TYPE.UPDATE or event_type == FN_EVENT_TYPE.CREATE:
        product_data = event.data.after.to_dict()

    if event_type == FN_EVENT_TYPE.DELETE:
        product_data = event.data.before.to_dict()

    if not product_data:
        raise ValueError(
            f"Product data is not available. event_type={event_type}, event={event.id}"
        )

    product_id = product_data.get("id")
    product = FirestoreProduct(**product_data)
    product.id = product_id

    return product


def products_sync_handler(event: Event[DocumentSnapshot]) -> None:
    # Get the data from the event
    event_type = get_fn_event_type(event)
    product = get_product_from_event(event, event_type)

    # Create the pubsub stuff
    publisher = get_pubsub_publisher_client(True)
    bulk_topic_path = get_or_create_topic(
        publisher, BULK_TOPIC_NAME
    )
    trigger_topic_path = get_or_create_topic(
        publisher, TRIGGER_TOPIC_NAME
    )

    # Create the message payload
    message_payload = TriggerMessage(
        product_id=product.id,
        event_type=event_type,
    )

    # Send the payload to the bulk topic
    # Here is where we store our messages to be processed by the bulk function
    try:
        future = publisher.publish(
            bulk_topic_path,
            data=json.dumps({"data": message_payload.model_dump()}).encode("utf-8"),
            ordering_key=message_payload.product_id,
        )
        message_id = future.result()
        _logger.info(
            f"Published product to bulk typsense sync topic: {message_id} event.id={event.id}"
        )
    except Exception as e:
        _logger.error(f"Error publishing to bulk topic: {str(e)} event.id={event.id}")

    # Publish trigger message
    # This is how we trigger the bulk processing function to be called.
    # This will bombard the products_sync_bulk function with more messages than needed,
    # probably resulting in 429s and retrys, but it's the only way I can think of to trigger the function
    # when the firestore document is updated without having to provision an ever running cloud run instance.
    # Since it is triggered immediately, the bulk function will be called immediately so it is also the
    # fastest way to trigger the function and sync the data.
    # The only downside is that it will bombard the bulk function with more messages than needed, so we will get 429s in the logs.
    try:
        trigger_future = publisher.publish(
            trigger_topic_path, data=json.dumps({"trigger_it": True}).encode("utf-8")
        )
        trigger_message_id = trigger_future.result()
        _logger.info(
            f"Published trigger message for bulk typsense sync function: {trigger_message_id} event.id={event.id}"
        )
    except Exception as e:
        _logger.error(
            f"Error publishing to trigger topic: {str(e)} event.id={event.id}"
        )

    publisher.stop()
    del publisher

    # _logger.info(f"Published message to topic: {message_id} event.id={event.id}")


###################################################################################
################################ BULK HANDLER #####################################
###################################################################################
# This is the function that will be called by the bulk topic.
# It will pull messages from the bulk topic and process them.
# It will also report the chunks to the pipeline report.
###################################################################################


def get_product_to_bulk_topic_messages(
    subscriber: pubsub_v1.SubscriberClient, subscription_path: str, num_messages: int
) -> tuple[
    list[tuple[TriggerMessage, str]],
    list[tuple[TriggerMessage, str]],
]:
    res_upsert, res_delete = [], []

    start_pulling_time = time.time()
    try:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": num_messages},
            timeout=30,
        )
    except DeadlineExceeded:
        _logger.info(
            f"No messages available. Took {time.time() - start_pulling_time} seconds."
        )
        return [], []
    except Exception as e:
        _logger.error(
            f"Error pulling messages from subscription: {e}. Took {time.time() - start_pulling_time} seconds."
        )
        return res_upsert, res_delete

    if len(response.received_messages) == 0:
        _logger.info("No messages available.")
        return res_upsert, res_delete
    else:
        _logger.info(
            f"Pulled {len(response.received_messages)} / {num_messages} messages from subscription: {subscription_path}"
        )

    for received_message in response.received_messages:
        try:
            msg_data = json.loads(received_message.message.data.decode("utf-8"))
            msg = TriggerMessage(**msg_data.get("data", {}))
            if msg.event_type == FN_EVENT_TYPE.DELETE:
                res_delete.append((msg, received_message.ack_id))
            else:
                res_upsert.append((msg, received_message.ack_id))
        except Exception as e:
            _logger.error(
                f"Error parsing event in products_sync_bulk_handler: {e}. Message: {received_message.message.data.decode('utf-8')}"
            )
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": [received_message.ack_id],
                }
            )

    return res_upsert, res_delete


def products_sync_bulk_handler(event: Event[DocumentSnapshot]) -> None:
    subscriber = get_pubsub_subscriber_client()
    subscription_path = get_or_create_subscription(
        BULK_TOPIC_NAME, True, 120
    )

    # Number of messages to pull in one request
    NUM_MESSAGES = 40

    start_time = time.time()

    upsert_messages, delete_messages = get_product_to_bulk_topic_messages(
        subscriber, subscription_path, NUM_MESSAGES
    )
    
    # Upsert products
    if len(upsert_messages) > 0:
        # Get the products from firestore for each message
        fs_products: list[tuple[FirestoreProduct, bool, bool]] = []
        for message in upsert_messages:
            try:
                fs_products.append(
                    get_product_by_id(message[0].product_id)
                )
            except Exception as e:
                _logger.error(
                    f"Error getting product from firestore {message[0].product_id}: {e}"
                )
                continue

        # Create other_product_model product for each product
        another_model_products: list[FirestoreProduct, dict] = []
        for product in fs_products:
            try:
                another_model_products.append(
                    (
                        product,
                        get_another_model_from_product(product)
                    )
                )
            except Exception as e:
                continue

        # Upsert the products to other_product_model
        if len(another_model_products) > 0:
            # Adding it to firestore one by one to make the test simpler
            for product, another_model_product in another_model_products:
                upsert_product_by_id(
                    another_model_product["id"],
                    another_model_product,
                    "other_product_model"
                )
            _logger.info(f"Upserted {len(another_model_products)} products to the other collection")

        # Ack the messages
        subscriber.acknowledge(
            request={
                "subscription": subscription_path,
                "ack_ids": [message[1] for message in upsert_messages],
            }
        )

        _logger.info(f"Acknowledged {len(upsert_messages)} products to the other collection")

    # Delete products
    if len(delete_messages) > 0:
        document_ids = [message[0].product_id for message in delete_messages]
        try:
            # Deleting it from firestore to make the test simpler
            for document_id in document_ids:
                delete_product_by_id(
                    document_id,
                    "other_product_model"
                )
            _logger.info(
                f"Deleting {len(delete_messages)} products from other_product_model"
            )
        except Exception as e:
            # We are trying to delete one by one because the bulk delete has failed
            # This is a workaround to avoid the function to fail and not delete the other products
            # This fallback should not ever happen in production, but it's a good fallback to avoid the function to fail and not delete the other products
            # Also, sometimes when developing locally this might happen so this makes sure that the function does not fail and deletes the products it can
            _logger.error(
                f"Error deleting documents {document_ids}: {e}. Trying one by one."
            )

            for document_id in document_ids:
                try:
                    _logger.info(
                        f"Deleting document {document_id} in bulk fallback one by one"
                    )
                    
                    # Deleting it from firestore to make the test simpler
                    delete_product_by_id(
                        document_id,
                        "other_product_model"
                    )
                except Exception as e:
                    _logger.error(
                        f"Error deleting document {document_id} in one by one fallback after bulk delete failed: {e}"
                    )

        subscriber.acknowledge(
            request={
                "subscription": subscription_path,
                "ack_ids": [message[1] for message in delete_messages],
            }
        )

        _logger.info(
            f"Deleted and acknowledged {len(delete_messages)} products from other_product_model"
        )

    end_time = time.time()
    _logger.info(
        f"Products to other_product_model bulk handler took {end_time - start_time} seconds"
    )

 