from typing import Optional
from datetime import datetime
import uuid
from typing import List

from sqlalchemy import or_, cast, String
from fastapi_filter.contrib.sqlalchemy import Filter

from app.orders.models import Order, OrderDetail, OrderProductLink, OrderStatus


class OrderFilter(Filter):
    # Filtering fields
    status: Optional[OrderStatus] = None
    status__in: Optional[List[OrderStatus]] = None

    created_at__gte: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None

    # Filter by product id in product_links (accept single or comma-separated list)
    product_links__product_id: Optional[List[uuid.UUID]] = None

    # Search across several fields (id, detail.email, detail.phone, external_id)
    search: Optional[str] = None

    # Ordering (use `order_by` query parameter)
    order_by: Optional[List[str]] = None

    class Constants(Filter.Constants):
        model = Order
        # We'll handle nested `detail` fields in the custom filter method below
        search_model_fields = ["id", "external_id", "detail.email", "detail.phone"]

    def filter(self, query):
        # Handle product_links.product_id and nested search for detail fields,
        # fall back to parent implementation for other fields.

        for field_name, value in self.filtering_fields:
            if field_name == "product_links__product_id":
                if not value:
                    continue
                vals = value if isinstance(value, list) else [value]
                query = query.filter(
                    Order.product_links.any(OrderProductLink.product_id.in_(vals))
                )
                continue

            if (
                field_name == self.Constants.search_field_name
                and value
                and hasattr(self.Constants, "search_model_fields")
            ):
                search_filters = []
                for field in self.Constants.search_model_fields:
                    if field.startswith("detail."):
                        # nested detail field
                        _, detail_field = field.split(".", 1)
                        search_filters.append(
                            Order.detail.has(
                                getattr(OrderDetail, detail_field).ilike(f"%{value}%")
                            )
                        )
                    else:
                        if field == "id":
                            search_filters.append(
                                cast(
                                    getattr(self.Constants.model, field), String
                                ).ilike(f"%{value}%")
                            )
                        else:
                            search_filters.append(
                                getattr(self.Constants.model, field).ilike(f"%{value}%")
                            )

                query = query.filter(or_(*search_filters))
                continue

            # Delegate other filters to base implementation by reusing the same logic
            # Build a single-field Filter and apply its filter logic.
            # Use parent Filter.filter by constructing a temporary Filter instance with only that field.
            # Simpler: let parent implementation handle remaining fields once by composing a dict.

        # After handling special cases above, delegate remaining fields to parent.
        remaining = self.model_dump(exclude_none=True, exclude_unset=True)
        # remove fields we already handled
        remaining.pop("product_links__product_id", None)
        remaining.pop(self.Constants.search_field_name, None)

        if remaining:
            temp = self.__class__(**remaining)
            return super(self.__class__, temp).filter(query)

        return query
