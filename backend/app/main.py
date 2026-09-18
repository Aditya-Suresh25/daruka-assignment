from datetime import datetime, timedelta
from enum import Enum
import os
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic_settings import BaseSettings
from shapely.geometry import shape, mapping
from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/darukaa"
    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Base(DeclarativeBase):
    pass


class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class ProjectType(str, Enum):
    CARBON = "Carbon"
    BIODIVERSITY = "Biodiversity"
    BOTH = "Carbon + Biodiversity"


class ProjectStatus(str, Enum):
    PLANNING = "Planning"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.USER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    project_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default=ProjectStatus.PLANNING.value)
    location_summary: Mapped[str] = mapped_column(String(160), default="")
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    sites: Mapped[list["Site"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Site(Base):
    __tablename__ = "sites"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    geometry = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True), nullable=False)
    area_hectares: Mapped[float] = mapped_column(Float, default=0)
    latitude: Mapped[float] = mapped_column(Float, default=0)
    longitude: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    project: Mapped[Project] = relationship(back_populates="sites")
    metrics: Mapped[list["SiteMetric"]] = relationship(
        back_populates="site", cascade="all, delete-orphan"
    )


class SiteMetric(Base):
    __tablename__ = "site_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    recorded_date: Mapped[datetime] = mapped_column(Date, index=True)
    carbon_stock: Mapped[float] = mapped_column(Float)
    carbon_sequestered: Mapped[float] = mapped_column(Float)
    biodiversity_index: Mapped[float] = mapped_column(Float)
    vegetation_cover: Mapped[float] = mapped_column(Float)
    project_health: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    site: Mapped[Site] = relationship(back_populates="metrics")


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    project_type: ProjectType
    status: ProjectStatus = ProjectStatus.PLANNING
    location_summary: str = ""
    start_date: datetime | None = None
    end_date: datetime | None = None


class ProjectOut(ProjectIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    site_count: int = 0


class SiteIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    geometry: dict


class SiteOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: str
    area_hectares: float
    latitude: float
    longitude: float
    geometry: dict
    created_at: datetime


class MetricIn(BaseModel):
    recorded_date: datetime
    carbon_stock: float = Field(ge=0)
    carbon_sequestered: float = Field(ge=0)
    biodiversity_index: float = Field(ge=0, le=100)
    vegetation_cover: float = Field(ge=0, le=100)
    project_health: float = Field(ge=0, le=100)
    notes: str = ""


class MetricOut(MetricIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def token_for(user: User) -> str:
    expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user.id), "exp": expires},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user = db.get(User, int(payload["sub"]))
    except (JWTError, TypeError, ValueError, KeyError):
        raise HTTPException(401, "Invalid or expired authentication token")
    if not user:
        raise HTTPException(401, "Invalid or expired authentication token")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != Role.ADMIN.value:
        raise HTTPException(403, "Administrator access required")
    return user


def site_response(site: Site) -> SiteOut:
    geometry = mapping(to_shape(site.geometry))
    return SiteOut(
        id=site.id,
        project_id=site.project_id,
        name=site.name,
        description=site.description,
        area_hectares=site.area_hectares,
        latitude=site.latitude,
        longitude=site.longitude,
        geometry={"type": "Polygon", "coordinates": geometry["coordinates"]},
        created_at=site.created_at,
    )


def project_response(project: Project) -> ProjectOut:
    return ProjectOut.model_validate(
        {**ProjectOut.model_validate(project).model_dump(), "site_count": len(project.sites)}
    )


app = FastAPI(title="Darukaa.Earth API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
        Base.metadata.create_all(engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(409, "An account with this email already exists")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=Role.ADMIN.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=token_for(user), user=user)


@app.post("/api/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not pwd_context.verify(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return Token(access_token=token_for(user), user=user)


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@app.get("/api/projects", response_model=list[ProjectOut])
def projects(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[ProjectOut]:
    return [
        project_response(x)
        for x in db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    ]


@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectIn, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/api/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> ProjectOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project_response(project)


@app.put("/api/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for key, value in payload.model_dump().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project_response(project)


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()


@app.get("/api/projects/{project_id}/sites", response_model=list[SiteOut])
def project_sites(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> list[SiteOut]:
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    return [
        site_response(x)
        for x in db.scalars(select(Site).where(Site.project_id == project_id)).all()
    ]


@app.post("/api/projects/{project_id}/sites", response_model=SiteOut, status_code=201)
def create_site(
    project_id: int,
    payload: SiteIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SiteOut:
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    try:
        polygon = shape(payload.geometry)
    except Exception as exc:
        raise HTTPException(422, "Invalid GeoJSON geometry") from exc
    if (
        polygon.geom_type != "Polygon"
        or polygon.is_empty
        or not polygon.is_valid
        or not polygon.exterior.is_ring
    ):
        raise HTTPException(422, "Geometry must be a valid, non-empty Polygon")
    centroid = polygon.centroid
    site = Site(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        geometry=from_shape(polygon, srid=4326),
        latitude=centroid.y,
        longitude=centroid.x,
    )
    db.add(site)
    db.flush()
    site.area_hectares = float(
        db.scalar(
            select(func.ST_Area(func.ST_Transform(site.geometry, 6933)) / 10000).where(
                Site.id == site.id
            )
        )
        or 0
    )
    db.commit()
    db.refresh(site)
    return site_response(site)


@app.get("/api/sites/{site_id}", response_model=SiteOut)
def get_site(
    site_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> SiteOut:
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    return site_response(site)


@app.put("/api/sites/{site_id}", response_model=SiteOut)
def update_site(
    site_id: int, payload: SiteIn, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> SiteOut:
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    try:
        polygon = shape(payload.geometry)
    except Exception as exc:
        raise HTTPException(422, "Invalid GeoJSON geometry") from exc
    if (
        polygon.geom_type != "Polygon"
        or polygon.is_empty
        or not polygon.is_valid
        or not polygon.exterior.is_ring
    ):
        raise HTTPException(422, "Geometry must be a valid, non-empty Polygon")
    centroid = polygon.centroid
    site.name = payload.name
    site.description = payload.description
    site.geometry = from_shape(polygon, srid=4326)
    site.latitude = centroid.y
    site.longitude = centroid.x
    db.flush()
    site.area_hectares = float(
        db.scalar(
            select(func.ST_Area(func.ST_Transform(site.geometry, 6933)) / 10000).where(
                Site.id == site.id
            )
        )
        or 0
    )
    db.commit()
    db.refresh(site)
    return site_response(site)


@app.delete("/api/sites/{site_id}", status_code=204)
def delete_site(
    site_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    db.delete(site)
    db.commit()


@app.get("/api/sites/geojson")
def sites_geojson(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": s.id,
                "geometry": site_response(s).geometry,
                "properties": {
                    "id": s.id,
                    "name": s.name,
                    "project_id": s.project_id,
                    "area_hectares": s.area_hectares,
                },
            }
            for s in db.scalars(select(Site)).all()
        ],
    }


@app.get("/api/sites/{site_id}/analytics", response_model=list[MetricOut])
def analytics(
    site_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> list[SiteMetric]:
    if not db.get(Site, site_id):
        raise HTTPException(404, "Site not found")
    return db.scalars(
        select(SiteMetric).where(SiteMetric.site_id == site_id).order_by(SiteMetric.recorded_date)
    ).all()


@app.post("/api/sites/{site_id}/analytics", response_model=MetricOut, status_code=201)
def add_metric(
    site_id: int, payload: MetricIn, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> SiteMetric:
    if not db.get(Site, site_id):
        raise HTTPException(404, "Site not found")
    metric = SiteMetric(site_id=site_id, **payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@app.get("/api/dashboard/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    projects = db.scalars(select(Project)).all()
    sites = db.scalars(select(Site)).all()
    metrics = db.scalars(select(SiteMetric).order_by(SiteMetric.recorded_date)).all()
    return {
        "total_projects": len(projects),
        "active_projects": sum(p.status == "Active" for p in projects),
        "total_sites": len(sites),
        "total_area": round(sum(s.area_hectares for s in sites), 2),
        "carbon_sequestered": round(sum(m.carbon_sequestered for m in metrics), 1),
        "average_biodiversity": (
            round(sum(m.biodiversity_index for m in metrics) / len(metrics), 1) if metrics else 0
        ),
    }
