"""merge gamification and existing heads

Revision ID: f849767fe6ee
Revises: a1b2c3d4e5f6, f79b481cd9b5
Create Date: 2025-12-13 02:47:34.689544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f849767fe6ee'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'f79b481cd9b5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
