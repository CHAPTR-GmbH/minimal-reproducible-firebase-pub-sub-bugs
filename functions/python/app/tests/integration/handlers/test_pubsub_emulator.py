# ruff: noqa: E402
import uuid
import pytest


def get_other_product_model_by_id(firestore_client, id: str) -> dict | None:
    try:
        res = firestore_client.collection("other_product_model").document(
            id
        ).get()
        # We are replacing the other_product_model with another firestore collection to make the setup simpler

        if not res.exists:
            return None
        return res
    except Exception as e:
        # print(f"get_other_product_model_by_id Exception: {e}")
        return None


def always_the_same_test(
    firestore_client,
    dummy_product,
    wait_until,
    num_products=100,
):
    ids = []
    for i in range(num_products):
        id = str(uuid.uuid4())

        firestore_client.collection("products").document(
            id
        ).set(
            {
                **dummy_product.model_dump(),
                "id": id,
            }
        )

        ids.append(id)

        # Now lets delete the first half of the products we added just to spice it up a bit
        remaining_ids = []
        if i % 10 == 0:

            # Lets check the state now
            for id in ids:
                wait_until(
                    lambda: get_other_product_model_by_id(firestore_client, id)
                    is not None,
                    timeout=30,
                    interval=1,
                )

            deleted_ids = []
            for j, id in enumerate(ids):
                if j <= len(ids) // 2:
                    firestore_client.collection(
                        "products"
                    ).document(id).delete()
                    deleted_ids.append(id)
                else:
                    remaining_ids.append(id)
            ids = remaining_ids


            for id in deleted_ids:
                print(f"Waiting for {id} to be deleted out of {i} products")
                wait_until(
                    lambda: get_other_product_model_by_id(firestore_client, id) is None,
                    timeout=30,
                    interval=1,
                )

    for id in ids:
        firestore_client.collection("products").document(
            id
        ).delete()

    for id in ids:
        wait_until(
            lambda: get_other_product_model_by_id(firestore_client, id) is None,
            timeout=30,
            interval=1,
        )


def test_adds_and_deletes_a_single_product(
    firestore_client,
    dummy_product,
    wait_until,
):
    always_the_same_test(
        firestore_client, 
        dummy_product, 
        wait_until, 
        num_products=1
    )

# @pytest.mark.skip(reason="Skipping test")
def test_adds_and_deletes_a_hundred_products_on_second_time(
    firestore_client,
    dummy_product,
    wait_until,
):
    always_the_same_test(
        firestore_client, 
        dummy_product, 
        wait_until
    )


@pytest.mark.skip(reason="Skipping test")
def test_adds_and_deletes_a_hundred_products_on_third_time(
    firestore_client,
    dummy_product,
    wait_until,
):
    always_the_same_test(
        firestore_client, 
        dummy_product, 
        wait_until
    )


@pytest.mark.skip(reason="Skipping test")
def test_adds_and_deletes_a_hundred_products_on_fourth_time(
    firestore_client,
    dummy_product,
    wait_until,
):
    always_the_same_test(
        firestore_client, 
        dummy_product, 
        wait_until
    )


@pytest.mark.skip(reason="Skipping test")
def test_adds_and_deletes_a_hundred_products_on_fifth_time(
    firestore_client,
    dummy_product,
    wait_until,
):
    always_the_same_test(
        firestore_client, 
        dummy_product, 
        wait_until
    )


@pytest.mark.skip(reason="Skipping test")
def test_adds_and_deletes_a_hundred_products_on_sixth_time(
    firestore_client,
    dummy_product,
    wait_until,
):
    always_the_same_test(
        firestore_client, 
        dummy_product, 
        wait_until
    )
