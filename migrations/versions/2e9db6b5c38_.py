"""empty message

Revision ID: 2e9db6b5c38
Revises: ad2c15555b
Create Date: 2015-07-13 20:40:01.026988

"""

# revision identifiers, used by Alembic.
revision = '2e9db6b5c38'
down_revision = 'ad2c15555b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ff_plans', sa.Column('name', sa.String(length=128), nullable=True))
    op.add_column('pp_plans', sa.Column('name', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pp_plans', 'name')
    op.drop_column('ff_plans', 'name')
    ### end Alembic commands ###
