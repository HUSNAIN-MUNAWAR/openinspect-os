from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from apps.api.openinspect_api.database import Base
from apps.api.openinspect_api.models import Organization, Facility

def test_tenant_scoped_query(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'db.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        a=Organization(name='A'); b=Organization(name='B'); db.add_all([a,b]); db.flush()
        db.add_all([Facility(organization_id=a.id,name='Alpha'),Facility(organization_id=b.id,name='Beta')]); db.commit()
        names=[x.name for x in db.scalars(select(Facility).where(Facility.organization_id==a.id)).all()]
        assert names == ['Alpha']
