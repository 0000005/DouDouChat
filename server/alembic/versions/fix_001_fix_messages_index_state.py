"""fix_messages_index_state

This migration ensures the database state is consistent across different environments.
Some environments may or may not have the idx_messages_friend_id index.
This migration does nothing as the index removal was already handled
(either by the original migration or it never existed).

Revision ID: fix_001
Revises: 0a8be336eb20
Create Date: 2026-01-05 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_001'
down_revision: Union[str, Sequence[str], None] = '0a8be336eb20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    No-op migration.
    This ensures consistency across environments where idx_messages_friend_id
    may or may not have existed before migration 7fa2b40a0479.
    """
    # Check if the index exists and drop it if so (safe operation)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes('messages')]
    
    if 'idx_messages_friend_id' in indexes:
        with op.batch_alter_table('messages', schema=None) as batch_op:
            batch_op.drop_index('idx_messages_friend_id')


def downgrade() -> None:
    """Downgrade is a no-op since we're just ensuring consistency."""
    pass
