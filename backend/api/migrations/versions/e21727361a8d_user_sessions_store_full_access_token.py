"""user_sessions store full access token

Revision ID: e21727361a8d
Revises: b7f4a1c9d2e3
Create Date: 2026-04-18 15:25:23.655728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e21727361a8d'
down_revision: Union[str, None] = 'b7f4a1c9d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("user_sessions")}
    if "access_token" not in columns:
        op.add_column("user_sessions", sa.Column("access_token", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("user_sessions")}
    if "access_token" in columns:
        op.drop_column("user_sessions", "access_token")
