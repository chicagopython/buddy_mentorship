from .base import *

DJANGO_LOG_LEVEL = "DEBUG"

import os

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {"console": {"class": "logging.StreamHandler",},},
#     "root": {"handlers": ["console"], "level": "WARNING",},
#     "loggers": {
#         "django": {
#             "handlers": ["console"],
#             "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
#             "propagate": False,
#         },
#     },
# }
