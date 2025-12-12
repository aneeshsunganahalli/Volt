"""Merge heads

Revision ID: 97562ee7cd8f
Revises: 1152dcc7f6df, 903ee38b1430
Create Date: 2025-12-12 22:38:04.223845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97562ee7cd8f'
down_revision: Union[str, Sequence[str], None] = ('1152dcc7f6df', '903ee38b1430')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
