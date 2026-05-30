import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.orders.router import validate_order_products
from app.orders.schemas import OrderProductLinkCreate


def make_product(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "name": "Test Product",
        "is_active": True,
        "is_available": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_link(product_id: uuid.UUID | None = None, quantity: int = 1) -> OrderProductLinkCreate:
    return OrderProductLinkCreate(
        product_id=product_id or uuid.uuid4(),
        quantity=quantity,
    )


def test_validate_order_products_success():
    product = make_product()
    link = make_link(product_id=product.id)

    validate_order_products([link], [product])


def test_validate_order_products_multiple_valid():
    product_a = make_product(name="Product A")
    product_b = make_product(name="Product B")
    links = [
        make_link(product_id=product_a.id, quantity=2),
        make_link(product_id=product_b.id, quantity=1),
    ]

    validate_order_products(links, [product_a, product_b])


def test_validate_order_products_missing_product():
    missing_id = uuid.uuid4()
    link = make_link(product_id=missing_id)

    with pytest.raises(HTTPException) as exc:
        validate_order_products([link], [])

    assert exc.value.status_code == 404
    assert str(missing_id) in exc.value.detail


def test_validate_order_products_partial_missing():
    product = make_product(name="Available product")
    missing_id = uuid.uuid4()
    links = [
        make_link(product_id=product.id),
        make_link(product_id=missing_id),
    ]

    with pytest.raises(HTTPException) as exc:
        validate_order_products(links, [product])

    assert exc.value.status_code == 404
    assert str(missing_id) in exc.value.detail


def test_validate_order_products_inactive():
    product = make_product(name="Inactive product", is_active=False)
    link = make_link(product_id=product.id)

    with pytest.raises(HTTPException) as exc:
        validate_order_products([link], [product])

    assert exc.value.status_code == 400
    assert "Inactive product" in exc.value.detail
    assert "not available for order" in exc.value.detail


def test_validate_order_products_unavailable():
    product = make_product(name="Unavailable product", is_available=False)
    link = make_link(product_id=product.id)

    with pytest.raises(HTTPException) as exc:
        validate_order_products([link], [product])

    assert exc.value.status_code == 400
    assert "Unavailable product" in exc.value.detail


def test_validate_order_products_inactive_and_unavailable():
    product = make_product(
        name="Disabled product",
        is_active=False,
        is_available=False,
    )
    link = make_link(product_id=product.id)

    with pytest.raises(HTTPException) as exc:
        validate_order_products([link], [product])

    assert exc.value.status_code == 400
    assert "Disabled product" in exc.value.detail
