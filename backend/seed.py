from datetime import date
from app.main import (
    Base,
    Project,
    ProjectStatus,
    ProjectType,
    SessionLocal,
    Site,
    SiteMetric,
    User,
    engine,
    from_shape,
    hash_password,
)
from shapely.geometry import Polygon

Base.metadata.create_all(engine)
db = SessionLocal()
try:
    if db.query(User).count() == 0:
        db.add(
            User(
                name="Demo Admin",
                email="admin@darukaa.earth",
                password_hash=hash_password("demo-password-2026"),
                role="ADMIN",
            )
        )
    if db.query(Project).count() == 0:
        names = [
            ("Western Ghats Restoration", ProjectType.BOTH.value, "Kerala, India"),
            ("Sundarbans Blue Carbon", ProjectType.CARBON.value, "West Bengal, India"),
            ("Deccan Biodiversity Corridor", ProjectType.BIODIVERSITY.value, "Maharashtra, India"),
            ("Konkan Mangrove Recovery", ProjectType.BOTH.value, "Goa, India"),
            ("Central India Forest Carbon", ProjectType.CARBON.value, "Madhya Pradesh, India"),
        ]
        for project_index, (name, project_type, location) in enumerate(names):
            project = Project(
                name=name,
                description="Synthetic demo project for environmental intelligence workflows.",
                project_type=project_type,
                status=(
                    ProjectStatus.ACTIVE.value
                    if project_index < 3
                    else ProjectStatus.PLANNING.value
                ),
                location_summary=location,
            )
            db.add(project)
            db.flush()
            for site_index in range(2 + (project_index % 3)):
                longitude = 73.4 + project_index * 1.1 + site_index * 0.04
                latitude = 11.2 + project_index * 2.2 + site_index * 0.05
                polygon = Polygon(
                    [
                        (longitude, latitude),
                        (longitude + 0.06, latitude + 0.01),
                        (longitude + 0.05, latitude + 0.06),
                        (longitude - 0.01, latitude + 0.04),
                        (longitude, latitude),
                    ]
                )
                site = Site(
                    project_id=project.id,
                    name=f"{name.split()[0]} monitoring block {site_index + 1}",
                    description="Fictional monitoring boundary for demo use.",
                    geometry=from_shape(polygon, srid=4326),
                    area_hectares=0,
                    latitude=latitude + 0.025,
                    longitude=longitude + 0.025,
                )
                db.add(site)
                db.flush()
                for metric_index in range(8):
                    db.add(
                        SiteMetric(
                            site_id=site.id,
                            recorded_date=date(
                                2024 + (metric_index // 4), ((metric_index % 4) * 3) + 1, 15
                            ),
                            carbon_stock=180 + project_index * 22 + metric_index * 7.3,
                            carbon_sequestered=14 + metric_index * 1.8,
                            biodiversity_index=58 + project_index * 2 + metric_index * 1.5,
                            vegetation_cover=44 + metric_index * 3.1,
                            project_health=70 + metric_index * 2.5,
                            notes="Synthetic demo observation",
                        )
                    )
    db.commit()
finally:
    db.close()
print("Seed complete. Demo login: admin@darukaa.earth / demo-password-2026")
