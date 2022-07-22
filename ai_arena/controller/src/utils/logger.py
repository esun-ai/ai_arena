import sys
import os
import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

logger_name = os.environ["LOGGER_NAME"]
env = os.environ["ENV"]

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.WARNING)

logger = logging.getLogger(logger_name)
logger.setLevel(logging.INFO)

if env != "test":
    client = google.cloud.logging.Client()
    gcloud_logging_handler = CloudLoggingHandler(client, name=logger_name)
    logger.addHandler(gcloud_logging_handler)
logger.addHandler(stream_handler)