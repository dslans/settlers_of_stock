"""Initial database schema

Revision ID: fe308690bd59
Revises: 
Create Date: 2025-09-11 21:51:15.704303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe308690bd59'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_active', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create watchlists table
    op.create_table('watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watchlists_id'), 'watchlists', ['id'], unique=False)
    op.create_index(op.f('ix_watchlists_user_id'), 'watchlists', ['user_id'], unique=False)

    # Create watchlist_items table
    op.create_table('watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('target_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('entry_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('shares_owned', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watchlist_items_id'), 'watchlist_items', ['id'], unique=False)
    op.create_index(op.f('ix_watchlist_items_symbol'), 'watchlist_items', ['symbol'], unique=False)
    op.create_index(op.f('ix_watchlist_items_watchlist_id'), 'watchlist_items', ['watchlist_id'], unique=False)

    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('alert_type', sa.Enum('PRICE_ABOVE', 'PRICE_BELOW', 'PRICE_CHANGE_PERCENT', 'VOLUME_SPIKE', 'TECHNICAL_BREAKOUT', 'TECHNICAL_BREAKDOWN', 'RSI_OVERBOUGHT', 'RSI_OVERSOLD', 'MOVING_AVERAGE_CROSS', 'NEWS_SENTIMENT', 'EARNINGS_DATE', 'ANALYST_UPGRADE', 'ANALYST_DOWNGRADE', name='alerttype'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'TRIGGERED', 'PAUSED', 'EXPIRED', 'CANCELLED', name='alertstatus'), nullable=False),
        sa.Column('condition_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('condition_operator', sa.String(length=10), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('message_template', sa.Text(), nullable=True),
        sa.Column('notify_email', sa.Boolean(), nullable=False),
        sa.Column('notify_push', sa.Boolean(), nullable=False),
        sa.Column('notify_sms', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_triggers', sa.Integer(), nullable=False),
        sa.Column('trigger_count', sa.Integer(), nullable=False),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_symbol'), 'alerts', ['symbol'], unique=False)
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)

    # Create alert_triggers table
    op.create_table('alert_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('trigger_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('market_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=False),
        sa.Column('push_sent', sa.Boolean(), nullable=False),
        sa.Column('sms_sent', sa.Boolean(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('trigger_metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_triggers_alert_id'), 'alert_triggers', ['alert_id'], unique=False)
    op.create_index(op.f('ix_alert_triggers_id'), 'alert_triggers', ['id'], unique=False)

    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('primary_symbols', sa.JSON(), nullable=True),
        sa.Column('analysis_types', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', 'ERROR', name='messagetype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='messagestatus'), nullable=False),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('symbols_mentioned', sa.JSON(), nullable=True),
        sa.Column('analysis_performed', sa.JSON(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

    # Create chat_contexts table
    op.create_table('chat_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('context_key', sa.String(length=100), nullable=False),
        sa.Column('context_data', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_contexts_context_key'), 'chat_contexts', ['context_key'], unique=False)
    op.create_index(op.f('ix_chat_contexts_id'), 'chat_contexts', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table('chat_contexts')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('alert_triggers')
    op.drop_table('alerts')
    op.drop_table('watchlist_items')
    op.drop_table('watchlists')
    op.drop_table('users')
