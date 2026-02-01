"""Order status

Revision ID: e31bde81997a
Revises: d87105c9f73e
Create Date: 2026-02-01 14:14:25.903195

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "e31bde81997a"
down_revision: Union[str, Sequence[str], None] = "d87105c9f73e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

new_type = sa.Enum(
    "CREATED", "CANCELLED", "SUCCESS", "ERROR", "PAID", name="orderstatus"
)
old_type = sa.Enum("CREATED", "CANCELLED", "SUCCESS", name="orderstatus")
tcr = sa.sql.table("order", sa.Column("status", new_type, nullable=False))


def upgrade():
    op.alter_column("order", "status", type_=new_type, existing_type=old_type)


def downgrade():
    op.execute(
        tcr.update()
        .where(tcr.c.status == "ERROR")
        .values(status="CANCELLED")
        .where(tcr.c.status == "PAID")
        .values(status="SUCCESS")
    )
    op.alter_column("order", "status", type_=old_type, existing_type=new_type)
