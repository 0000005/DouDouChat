"""add_friend_model_settings

Revision ID: 2f3c9b8c4f2a
Revises: caab3b9a757e
Create Date: 2026-01-20 10:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f3c9b8c4f2a'
down_revision: Union[str, Sequence[str], None] = 'caab3b9a757e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Changes:
    1. Add temperature column to friends
    2. Add top_p column to friends
    """
    with op.batch_alter_table('friends', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('temperature', sa.Float(), nullable=False, server_default=sa.text('0.8'))
        )
        batch_op.add_column(
            sa.Column('top_p', sa.Float(), nullable=False, server_default=sa.text('0.9'))
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('friends', schema=None) as batch_op:
        batch_op.drop_column('top_p')
        batch_op.drop_column('temperature')
