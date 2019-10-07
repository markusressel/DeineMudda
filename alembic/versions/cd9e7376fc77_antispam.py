"""antispam

Revision ID: cd9e7376fc77
Revises: 4234af1808b8
Create Date: 2019-10-07 16:20:30.799398

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'cd9e7376fc77'
down_revision = '4234af1808b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('last_timeout', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'last_timeout')
    op.drop_column('users', 'is_banned')
    # ### end Alembic commands ###
