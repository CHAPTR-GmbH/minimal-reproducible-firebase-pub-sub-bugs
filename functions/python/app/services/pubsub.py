import json
import logging
from typing import Any, Dict

from google.cloud import pubsub_v1
from google.api_core.retry import Retry
from google.cloud.pubsub_v1.publisher.futures import Future


_logger = logging.getLogger(__name__)

_pubsub_publisher_client = None
_pubsub_subscriber_client = None


def get_pubsub_publisher_client(
    enable_message_ordering: bool = False
) -> pubsub_v1.PublisherClient:
    if _pubsub_publisher_client is not None:
        return _pubsub_publisher_client

    if not enable_message_ordering:
        return pubsub_v1.PublisherClient()

    return pubsub_v1.PublisherClient(
        publisher_options=pubsub_v1.types.PublisherOptions(
            enable_message_ordering=True,
        )
    )


def get_pubsub_subscriber_client() -> pubsub_v1.SubscriberClient:
    if _pubsub_subscriber_client is not None:
        return _pubsub_subscriber_client

    return pubsub_v1.SubscriberClient()


def get_topic_path(project_id: str, topic_id: str) -> str:
    pubsub_client = get_pubsub_publisher_client()
    return pubsub_client.topic_path(project_id, topic_id)


def get_or_create_topic(
    publisher: pubsub_v1.PublisherClient,
    topic_name: str,
) -> str:
    topic_path = get_topic_path("demo-local-development", topic_name)

    try:
        publisher.get_topic(request={"topic": topic_path})
        _logger.info(f"Topic {topic_path} already exists")
    except Exception:
        publisher.create_topic(
            request={
                "name": topic_path,
            },
            retry=Retry(
                minimum_backoff="10s",
                maximum_backoff="600s",
            ),
        )

    return topic_path


def publish_message(
    topic_id: str,
    message_data: Dict[str, Any],
    attributes: Dict[str, str] = {},
) -> Future:
    pubsub_client = get_pubsub_publisher_client()
    topic_path = get_topic_path("demo-local-development", topic_id)

    try:
        message_bytes = json.dumps(message_data).encode("utf-8")
    except Exception:
        raise ValueError(
            f"Invalid message_data type: {type(message_data)}. Must be dict"
        )

    try:
        future = pubsub_client.publish(topic_path, data=message_bytes, **attributes)
        _logger.info(f"Published message to {topic_id} with ID: {future.result()}")
        # pubsub_client.stop()
        # del pubsub_client
        return future
    except Exception as e:
        _logger.error(f"Error publishing message to {topic_id}: {e}")
        raise e


def get_or_create_subscription(
    topic_name: str,
    enable_message_ordering: bool = False,
    ack_deadline_seconds: int = 120,
):
    subscriber = get_pubsub_subscriber_client()
    publisher = get_pubsub_publisher_client()

    # Define topic
    topic_path = get_or_create_topic(publisher, topic_name)

    # Define subscription
    subscription_name = f"{topic_name}-sub"
    subscription_path = subscriber.subscription_path(
        "demo-local-development", subscription_name
    )

    try:
        subscriber.get_subscription(request={"subscription": subscription_path})
        # _logger.info(f"Subscription {subscription_path} exists")
    except Exception:
        # _logger.info(
        #     f"Creating subscription {subscription_path} for topic {topic_path}"
        # )

        # Some emulator guardrails, topic should already exist on dev and prod
        try:
            subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "enable_message_ordering": enable_message_ordering,
                    "ack_deadline_seconds": ack_deadline_seconds,
                },
            )
        except Exception as e:
            _logger.error(f"Error creating subscription {subscription_path}: {e}")

    return subscription_path
