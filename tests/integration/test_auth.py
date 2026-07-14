from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openinspect_api.database import Base, get_db
from openinspect_api.main import app


def test_register_and_login(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'auth.db'}")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def override_db():
        with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        org = client.post('/organizations', json={'name': 'Auth Test Org'}).json()
        user = client.post('/auth/register', json={
            'organization_id': org['id'], 'email': 'inspector@example.com',
            'password': 'correct-horse-battery-staple', 'full_name': 'Inspector One', 'role': 'inspector'
        })
        assert user.status_code == 200
        token = client.post('/auth/token', json={'email': 'inspector@example.com', 'password': 'correct-horse-battery-staple'})
        assert token.status_code == 200
        assert token.json()['token_type'] == 'bearer'
    finally:
        app.dependency_overrides.clear()
