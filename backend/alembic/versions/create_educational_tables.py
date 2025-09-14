"""create_educational_tables

Revision ID: create_educational_tables
Revises: create_earnings_tables
Create Date: 2024-12-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_educational_tables'
down_revision = 'create_earnings_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create educational_concepts table
    op.create_table('educational_concepts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('concept_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False),
        sa.Column('short_description', sa.String(length=500), nullable=False),
        sa.Column('detailed_explanation', sa.Text(), nullable=False),
        sa.Column('practical_example', sa.Text(), nullable=True),
        sa.Column('formula', sa.String(length=200), nullable=True),
        sa.Column('interpretation_guide', sa.Text(), nullable=True),
        sa.Column('common_mistakes', sa.Text(), nullable=True),
        sa.Column('keywords', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_educational_concepts_id'), 'educational_concepts', ['id'], unique=False)
    op.create_index(op.f('ix_educational_concepts_name'), 'educational_concepts', ['name'], unique=True)

    # Create learning_paths table
    op.create_table('learning_paths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['concept_id'], ['educational_concepts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_learning_progress table
    op.create_table('user_learning_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('difficulty_rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['concept_id'], ['educational_concepts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create concept_relationships table for many-to-many relationships
    op.create_table('concept_relationships',
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['educational_concepts.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['educational_concepts.id'], ),
        sa.PrimaryKeyConstraint('parent_id', 'child_id')
    )


def downgrade():
    op.drop_table('concept_relationships')
    op.drop_table('user_learning_progress')
    op.drop_table('learning_paths')
    op.drop_index(op.f('ix_educational_concepts_name'), table_name='educational_concepts')
    op.drop_index(op.f('ix_educational_concepts_id'), table_name='educational_concepts')
    op.drop_table('educational_concepts')