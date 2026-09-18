from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("project_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("location_summary", sa.String(160)),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("geometry", Geometry("POLYGON", srid=4326), nullable=False),
        sa.Column("area_hectares", sa.Float),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("idx_sites_geometry", "sites", ["geometry"], postgresql_using="gist")
    op.create_table(
        "site_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "site_id", sa.Integer, sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("recorded_date", sa.Date, nullable=False),
        sa.Column("carbon_stock", sa.Float, nullable=False),
        sa.Column("carbon_sequestered", sa.Float, nullable=False),
        sa.Column("biodiversity_index", sa.Float, nullable=False),
        sa.Column("vegetation_cover", sa.Float, nullable=False),
        sa.Column("project_health", sa.Float, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime),
    )


def downgrade():
    op.drop_table("site_metrics")
    op.drop_index("idx_sites_geometry", table_name="sites")
    op.drop_table("sites")
    op.drop_table("projects")
    op.drop_table("users")
