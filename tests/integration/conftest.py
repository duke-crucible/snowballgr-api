"""
We use pytest-flask, which handles creating the
client and request contexts for testing.
"""
import os

import pytest
from prepare_test_data import load_test_data

from app.app import create_app


@pytest.fixture(scope="session")
def app():
    app = create_app(os.environ["SERVICE_APP_ENV"], testing=True)
    with app.app_context():
        load_test_data()
        yield app
