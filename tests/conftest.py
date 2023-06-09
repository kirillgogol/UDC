import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from test_01_users_api import USER_DATA, USER_DATA_FOR_UNOTHORIZED_ACCESS

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 

from app.db_config import Base, get_db
from main import users, articles, login, template_views


def start_app():
    app = FastAPI()
    app.include_router(users)
    app.include_router(articles)
    app.include_router(login)
    app.include_router(template_views)
    return app


SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass = StaticPool
)
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def app():
    Base.metadata.create_all(engine)
    app = start_app()
    yield app
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def db_session(app: FastAPI):
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)
    yield session 
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def client(app: FastAPI, db_session: SessionTesting):

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def token(client):
    response = client.post('/auth/login', data=USER_DATA)
    token = response.json()['access_token']
    yield token


@pytest.fixture(scope="module")
def unothorized_access_token(client):
    response = client.post('/auth/login', data=USER_DATA_FOR_UNOTHORIZED_ACCESS)
    unothorized_access_token = response.json()['access_token']
    yield unothorized_access_token