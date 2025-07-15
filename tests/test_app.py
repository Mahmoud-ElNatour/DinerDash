import os
import sys
import pathlib

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SKIP_BOOTSTRAP'] = '1'
os.environ['SESSION_SECRET'] = 'test-secret'

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app import app, db
import pytest

@pytest.fixture(autouse=True, scope='module')
def setup_database():
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()


def test_dashboard_requires_login():
    with app.test_client() as client:
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/auth/login' in resp.location
