"""empty message

Revision ID: 25da865a72b
Revises: 2a425ea7d49
Create Date: 2015-07-02 21:59:31.673930

"""

# revision identifiers, used by Alembic.
revision = '25da865a72b'
down_revision = '2a425ea7d49'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pp_parameters', sa.Column('load_scale_factor', sa.Float(), nullable=False))
    op.drop_column('pp_parameters', 'plan_scale_factor')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pp_parameters', sa.Column('plan_scale_factor', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.drop_column('pp_parameters', 'load_scale_factor')
    ### end Alembic commands ###
