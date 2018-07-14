"""empty message

Revision ID: e92b61c5d999
Revises: 
Create Date: 2018-07-14 16:16:27.385000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e92b61c5d999'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_users_user_name'), 'users', ['user_name'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_user_name'), table_name='users')
    # ### end Alembic commands ###
