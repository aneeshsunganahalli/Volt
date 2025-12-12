"""add gamification tables

Revision ID: a1b2c3d4e5f6
Revises: 67b35a1cdc38
Create Date: 2025-12-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '67b35a1cdc38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types using raw SQL to avoid conflicts
    conn = op.get_bind()
    
    # Create event_type enum if not exists
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE eventtype AS ENUM (
                'TRANSACTION_IMPORTED', 'TRANSACTION_CATEGORIZED', 'GOAL_CREATED',
                'GOAL_MILESTONE_REACHED', 'GOAL_COMPLETED', 'DAILY_CHECKIN',
                'NO_SPEND_DAY', 'BUDGET_UNDER_TARGET', 'SPENDING_REVIEW_COMPLETED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create streak_type enum if not exists
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE streaktype AS ENUM ('checkin', 'categorization', 'no_spend');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create badge_tier enum if not exists
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE badgetier AS ENUM ('bronze', 'silver', 'gold', 'platinum');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Reference the enums for table creation
    from sqlalchemy.dialects import postgresql
    event_type_enum = postgresql.ENUM(
        'TRANSACTION_IMPORTED', 'TRANSACTION_CATEGORIZED', 'GOAL_CREATED',
        'GOAL_MILESTONE_REACHED', 'GOAL_COMPLETED', 'DAILY_CHECKIN',
        'NO_SPEND_DAY', 'BUDGET_UNDER_TARGET', 'SPENDING_REVIEW_COMPLETED',
        name='eventtype', create_type=False
    )
    streak_type_enum = postgresql.ENUM(
        'checkin', 'categorization', 'no_spend',
        name='streaktype', create_type=False
    )
    badge_tier_enum = postgresql.ENUM(
        'bronze', 'silver', 'gold', 'platinum',
        name='badgetier', create_type=False
    )
    
    # Create achievements table
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tier', badge_tier_enum, nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=False),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
    op.create_index(op.f('ix_achievements_code'), 'achievements', ['code'], unique=True)
    
    # Create gamification_events table
    op.create_table(
        'gamification_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', event_type_enum, nullable=False),
        sa.Column('xp_awarded', sa.Integer(), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gamification_events_id'), 'gamification_events', ['id'], unique=False)
    op.create_index(op.f('ix_gamification_events_user_id'), 'gamification_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_gamification_events_created_at'), 'gamification_events', ['created_at'], unique=False)
    op.create_index('ix_gamification_events_user_type_date', 'gamification_events', ['user_id', 'event_type', 'created_at'], unique=False)
    
    # Create user_points table
    op.create_table(
        'user_points',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('xp_total', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # Create user_streaks table
    op.create_table(
        'user_streaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('streak_type', streak_type_enum, nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('last_date', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_streaks_id'), 'user_streaks', ['id'], unique=False)
    op.create_index(op.f('ix_user_streaks_user_id'), 'user_streaks', ['user_id'], unique=False)
    op.create_index('ix_user_streaks_user_type', 'user_streaks', ['user_id', 'streak_type'], unique=True)
    
    # Create user_achievements table
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_achievements_id'), 'user_achievements', ['id'], unique=False)
    op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)
    op.create_index('ix_user_achievements_user_achievement', 'user_achievements', ['user_id', 'achievement_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables
    op.drop_index('ix_user_achievements_user_achievement', table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_user_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_id'), table_name='user_achievements')
    op.drop_table('user_achievements')
    
    op.drop_index('ix_user_streaks_user_type', table_name='user_streaks')
    op.drop_index(op.f('ix_user_streaks_user_id'), table_name='user_streaks')
    op.drop_index(op.f('ix_user_streaks_id'), table_name='user_streaks')
    op.drop_table('user_streaks')
    
    op.drop_table('user_points')
    
    op.drop_index('ix_gamification_events_user_type_date', table_name='gamification_events')
    op.drop_index(op.f('ix_gamification_events_created_at'), table_name='gamification_events')
    op.drop_index(op.f('ix_gamification_events_user_id'), table_name='gamification_events')
    op.drop_index(op.f('ix_gamification_events_id'), table_name='gamification_events')
    op.drop_table('gamification_events')
    
    op.drop_index(op.f('ix_achievements_code'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_id'), table_name='achievements')
    op.drop_table('achievements')
    
    # Drop enum types
    sa.Enum(name='badgetier').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='streaktype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='eventtype').drop(op.get_bind(), checkfirst=True)
