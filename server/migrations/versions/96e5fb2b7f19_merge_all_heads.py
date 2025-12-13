"""merge_all_heads

Revision ID: 96e5fb2b7f19
Revises: f849767fe6ee, fea53fdbdb6d
Create Date: 2025-12-13 08:14:57.326565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96e5fb2b7f19'
down_revision: Union[str, Sequence[str], None] = ('f849767fe6ee', 'fea53fdbdb6d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
