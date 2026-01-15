"""update_chat_session_memory_fields

Revision ID: caab3b9a757e
Revises: 
Create Date: 2026-01-15 11:06:20.743323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caab3b9a757e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    Changes:
    1. Add memory_error column (TEXT, nullable)
    2. Change memory_generated from BOOLEAN to INTEGER
       Values: 0=未生成, 1=已生成, 2=生成失败
    """
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        # Add new column for error messages
        batch_op.add_column(sa.Column('memory_error', sa.Text(), nullable=True))
        
        # Change memory_generated from BOOLEAN to INTEGER
        # [Data Compatibility Note]
        # SQLite stores BOOLEAN as INTEGER (0/1). 
        # Old values: False(0), True(1) map directly to New values: Not Generated(0), Generated(1).
        # No explicit data conversion step is needed.
        batch_op.alter_column('memory_generated',
               existing_type=sa.BOOLEAN(),
               type_=sa.Integer(),
               existing_nullable=False,
               existing_server_default=sa.text('0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        # Revert memory_generated back to BOOLEAN
        batch_op.alter_column('memory_generated',
               existing_type=sa.Integer(),
               type_=sa.BOOLEAN(),
               existing_nullable=False,
               existing_server_default=sa.text('0'))
        
        # Drop the memory_error column
        batch_op.drop_column('memory_error')
