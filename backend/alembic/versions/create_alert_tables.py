"""Create alert tables

Revision ID: create_alert_tables
Revises: fe308690bd59
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_alert_tables'
down_revision = 'fe308690bd59'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create alert_type enum
    alert_type_enum = postgresql.ENUM(
        'price_above',
        'price_below', 
        'price_change_percent',
        'volume_spike',
        'technical_breakout',
        'technical_breakdown',
        'rsi_overbought',
        'rsi_oversold',
        'moving_average_cross',
        'news_sentiment',
        'earnings_date',
        'analyst_upgrade',
        'analyst_downgrade',
        name='alerttype'
    )
    alert_type_enum.create(op.get_bind())

    # Create alert_status enum
    alert_status_enum = postgresql.ENUM(
        'active',
        'triggered',
        'paused',
        'expired',
        'cancelled',
        name='alertstatus'
    )
    alert_status_enum.create(op.get_bind())

    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('alert_type', alert_type_enum, nullable=False),
        sa.Column('status', alert_status_enum, nullable=False, server_default='active'),
        sa.Column('condition_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('condition_operator', sa.String(length=10), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('message_template', sa.Text(), nullable=True),
        sa.Column('notify_email', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_push', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_sms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_triggers', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for alerts table
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('ix_alerts_symbol', 'alerts', ['symbol'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])
    op.create_index('ix_alerts_user_status', 'alerts', ['user_id', 'status'])
    op.create_index('ix_alerts_symbol_status', 'alerts', ['symbol', 'status'])
    
    # Create foreign key constraint
    op.create_foreign_key('fk_alerts_user_id', 'alerts', 'users', ['user_id'], ['id'])

    # Create alert_triggers table
    op.create_table('alert_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('trigger_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('market_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('push_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sms_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('trigger_metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for alert_triggers table
    op.create_index('ix_alert_triggers_id', 'alert_triggers', ['id'])
    op.create_index('ix_alert_triggers_alert_id', 'alert_triggers', ['alert_id'])
    op.create_index('ix_alert_triggers_triggered_at', 'alert_triggers', ['triggered_at'])
    
    # Create foreign key constraint
    op.create_foreign_key('fk_alert_triggers_alert_id', 'alert_triggers', 'alerts', ['alert_id'], ['id'])

    # Add trigger to update updated_at column on alerts table
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_alerts_updated_at 
        BEFORE UPDATE ON alerts 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_alerts_updated_at ON alerts;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop foreign key constraints
    op.drop_constraint('fk_alert_triggers_alert_id', 'alert_triggers', type_='foreignkey')
    op.drop_constraint('fk_alerts_user_id', 'alerts', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_alert_triggers_triggered_at', 'alert_triggers')
    op.drop_index('ix_alert_triggers_alert_id', 'alert_triggers')
    op.drop_index('ix_alert_triggers_id', 'alert_triggers')
    
    op.drop_index('ix_alerts_symbol_status', 'alerts')
    op.drop_index('ix_alerts_user_status', 'alerts')
    op.drop_index('ix_alerts_status', 'alerts')
    op.drop_index('ix_alerts_symbol', 'alerts')
    op.drop_index('ix_alerts_user_id', 'alerts')
    op.drop_index('ix_alerts_id', 'alerts')
    
    # Drop tables
    op.drop_table('alert_triggers')
    op.drop_table('alerts')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS alertstatus;")
    op.execute("DROP TYPE IF EXISTS alerttype;")