import logging
import sys

from flask_pymongo import PyMongo
from flask_restful import Api

# Create the flask restful API service
api = Api(prefix="/api", catch_all_404s=True)

mongo = PyMongo()

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("Snowball_GR")
