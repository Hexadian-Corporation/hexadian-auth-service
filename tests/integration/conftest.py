from collections.abc import Generator

import pytest
from pymongo import MongoClient
from pymongo.database import Database
from testcontainers.mongodb import MongoDbContainer


@pytest.fixture(scope="session")
def mongo_container() -> Generator[MongoDbContainer, None, None]:
    with MongoDbContainer("mongo:7") as container:
        yield container


@pytest.fixture(scope="session")
def mongo_url(mongo_container: MongoDbContainer) -> str:
    return mongo_container.get_connection_url()


@pytest.fixture(scope="session")
def mongo_client(mongo_container: MongoDbContainer) -> Generator[MongoClient, None, None]:
    client: MongoClient = MongoClient(mongo_container.get_connection_url())
    yield client
    client.close()


@pytest.fixture()
def db(mongo_client: MongoClient, mongo_url: str) -> Generator[Database, None, None]:
    """Function-scoped database — dropped after each test."""
    database = mongo_client["auth_integration_test"]
    database._mongo_url = mongo_url  # type: ignore[attr-defined]
    yield database
    mongo_client.drop_database("auth_integration_test")
