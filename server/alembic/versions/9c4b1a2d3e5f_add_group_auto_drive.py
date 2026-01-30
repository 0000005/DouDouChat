"""add_group_auto_drive

Revision ID: 9c4b1a2d3e5f
Revises: 8b7e6c3d2f1a
Create Date: 2026-01-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.types import UTCDateTime


# revision identifiers, used by Alembic.
revision: str = "9c4b1a2d3e5f"
down_revision: Union[str, Sequence[str], None] = "8b7e6c3d2f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("group_sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_type", sa.String(length=20), nullable=False, server_default="normal"))

    with op.batch_alter_table("group_messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("debate_side", sa.String(length=20), nullable=True))

    op.create_table(
        "group_auto_drive_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("topic_json", sa.JSON(), nullable=False),
        sa.Column("roles_json", sa.JSON(), nullable=False),
        sa.Column("turn_limit", sa.Integer(), nullable=False),
        sa.Column("end_action", sa.String(length=20), nullable=False),
        sa.Column("judge_id", sa.String(length=64), nullable=True),
        sa.Column("summary_by", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
        sa.Column("phase", sa.String(length=32), nullable=True),
        sa.Column("current_round", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_turn", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_speaker_id", sa.String(length=64), nullable=True),
        sa.Column("pause_reason", sa.String(length=128), nullable=True),
        sa.Column("started_at", UTCDateTime(), nullable=False),
        sa.Column("ended_at", UTCDateTime(), nullable=True),
        sa.Column("create_time", UTCDateTime(), nullable=False),
        sa.Column("update_time", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_group_auto_drive_runs_group_id_groups")),
        sa.ForeignKeyConstraint(["session_id"], ["group_sessions.id"], name=op.f("fk_group_auto_drive_runs_session_id_group_sessions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_auto_drive_runs")),
    )
    with op.batch_alter_table("group_auto_drive_runs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_group_auto_drive_runs_id"), ["id"], unique=False)
        batch_op.create_index("ix_group_auto_drive_runs_group_id", ["group_id"], unique=False)
        batch_op.create_index("ix_group_auto_drive_runs_session_id", ["session_id"], unique=False)

    conn = op.get_bind()
    conn.execute(sa.text("UPDATE group_sessions SET session_type = 'normal' WHERE session_type IS NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("group_auto_drive_runs", schema=None) as batch_op:
        batch_op.drop_index("ix_group_auto_drive_runs_session_id")
        batch_op.drop_index("ix_group_auto_drive_runs_group_id")
        batch_op.drop_index(batch_op.f("ix_group_auto_drive_runs_id"))

    op.drop_table("group_auto_drive_runs")

    with op.batch_alter_table("group_messages", schema=None) as batch_op:
        batch_op.drop_column("debate_side")

    with op.batch_alter_table("group_sessions", schema=None) as batch_op:
        batch_op.drop_column("session_type")
