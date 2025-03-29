"""create property table

Revision ID: 36b45ef19a73
Revises: 1a31ce608336
Create Date: 2025-03-29 09:13:05.333863

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import sqlalchemy.dialects.postgresql as postgresql

# revision identifiers, used by Alembic.
revision = '36b45ef19a73'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "property",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("zip_code", sa.String(length=20), nullable=False),
        sa.Column("bedrooms", sa.Integer, nullable=True),
        sa.Column("bathrooms", sa.Float, nullable=True),
        sa.Column("sqft", sa.Integer, nullable=True),
        sa.Column("lot_size", sa.Float, nullable=True),
        sa.Column("year_built", sa.Integer, nullable=True),
        sa.Column("list_price", sa.Float, nullable=True),
        sa.Column("high_school", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_table("property")
