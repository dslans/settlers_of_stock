"""Create earnings and corporate events tables

Revision ID: create_earnings_tables
Revises: create_alert_tables
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_earnings_tables'
down_revision = 'create_alert_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    earnings_confidence_enum = postgresql.ENUM(
        'high', 'medium', 'low', 'unconfirmed',
        name='earningsconfidence'
    )
    earnings_confidence_enum.create(op.get_bind())
    
    event_type_enum = postgresql.ENUM(
        'earnings', 'dividend', 'stock_split', 'merger', 'acquisition',
        'spinoff', 'rights_offering', 'special_dividend', 'conference_call',
        'analyst_day',
        name='eventtype'
    )
    event_type_enum.create(op.get_bind())
    
    event_impact_enum = postgresql.ENUM(
        'high', 'medium', 'low', 'unknown',
        name='eventimpact'
    )
    event_impact_enum.create(op.get_bind())
    
    # Create earnings_events table
    op.create_table(
        'earnings_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        
        # Event timing
        sa.Column('earnings_date', sa.DateTime(), nullable=False),
        sa.Column('report_time', sa.String(length=20), nullable=True),
        sa.Column('fiscal_quarter', sa.String(length=10), nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=True),
        
        # Estimates
        sa.Column('eps_estimate', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('eps_estimate_high', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('eps_estimate_low', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('eps_estimate_count', sa.Integer(), nullable=True),
        sa.Column('revenue_estimate', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('revenue_estimate_high', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('revenue_estimate_low', sa.Numeric(precision=15, scale=2), nullable=True),
        
        # Actuals
        sa.Column('eps_actual', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('revenue_actual', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('eps_surprise', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('revenue_surprise', sa.Numeric(precision=15, scale=2), nullable=True),
        
        # Metadata
        sa.Column('confidence', earnings_confidence_enum, nullable=True, default='medium'),
        sa.Column('impact_level', event_impact_enum, nullable=True, default='medium'),
        sa.Column('is_confirmed', sa.Boolean(), nullable=True, default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for earnings_events
    op.create_index('ix_earnings_events_symbol', 'earnings_events', ['symbol'])
    op.create_index('ix_earnings_events_earnings_date', 'earnings_events', ['earnings_date'])
    op.create_index('ix_earnings_events_symbol_date', 'earnings_events', ['symbol', 'earnings_date'])
    
    # Create corporate_events table
    op.create_table(
        'corporate_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        
        # Event details
        sa.Column('event_type', event_type_enum, nullable=False),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('ex_date', sa.DateTime(), nullable=True),
        sa.Column('record_date', sa.DateTime(), nullable=True),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        
        # Event-specific data
        sa.Column('dividend_amount', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('split_ratio', sa.String(length=20), nullable=True),
        sa.Column('split_factor', sa.Numeric(precision=10, scale=6), nullable=True),
        
        # Description and impact
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('impact_level', event_impact_enum, nullable=True, default='medium'),
        sa.Column('is_confirmed', sa.Boolean(), nullable=True, default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for corporate_events
    op.create_index('ix_corporate_events_symbol', 'corporate_events', ['symbol'])
    op.create_index('ix_corporate_events_event_date', 'corporate_events', ['event_date'])
    op.create_index('ix_corporate_events_event_type', 'corporate_events', ['event_type'])
    op.create_index('ix_corporate_events_symbol_type_date', 'corporate_events', ['symbol', 'event_type', 'event_date'])
    
    # Create earnings_historical_performance table
    op.create_table(
        'earnings_historical_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('earnings_event_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        
        # Performance metrics
        sa.Column('price_before_earnings', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_after_earnings', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_change_1d', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_1w', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_1m', sa.Numeric(precision=10, scale=4), nullable=True),
        
        sa.Column('volume_before', sa.Integer(), nullable=True),
        sa.Column('volume_after', sa.Integer(), nullable=True),
        sa.Column('volume_change', sa.Numeric(precision=10, scale=4), nullable=True),
        
        # Beat/miss patterns
        sa.Column('beat_estimate', sa.Boolean(), nullable=True),
        sa.Column('surprise_magnitude', sa.Numeric(precision=10, scale=4), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['earnings_event_id'], ['earnings_events.id'], ondelete='CASCADE')
    )
    
    # Create indexes for earnings_historical_performance
    op.create_index('ix_earnings_historical_performance_symbol', 'earnings_historical_performance', ['symbol'])
    op.create_index('ix_earnings_historical_performance_earnings_event_id', 'earnings_historical_performance', ['earnings_event_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('earnings_historical_performance')
    op.drop_table('corporate_events')
    op.drop_table('earnings_events')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS eventimpact')
    op.execute('DROP TYPE IF EXISTS eventtype')
    op.execute('DROP TYPE IF EXISTS earningsconfidence')