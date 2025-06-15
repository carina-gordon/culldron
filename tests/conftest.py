import os
import pytest
from sqlmodel import SQLModel, create_engine
from sqlalchemy.pool import StaticPool

@pytest.fixture(autouse=True)
def setup_test_database():
    """Create a test database in memory for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine 