"""empty message

Revision ID: 4a5df8c40b7
Revises: 768b490192
Create Date: 2015-06-10 11:50:13.446477

"""

# revision identifiers, used by Alembic.
revision = '4a5df8c40b7'
down_revision = '768b490192'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ff_parameters', sa.Column('plan_since_initial_p', postgresql.ARRAY(sa.Float()), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ff_parameters', 'plan_since_initial_p')
    ### end Alembic commands ###