import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

NBRB_BASE_URL = "https://api.nbrb.by/exrates/"

BASIC_VALUE_IN_BYN = os.getenv("BASIC_VALUE_IN_BYN")

CONNECTION_TIMEOUT = float(os.getenv("CONNECTION_TIMEOUT", 3))
CRM_DATABASE_PATH = os.getenv("CRM_DATABASE_PATH", "data/crm.sqlite3")
CRM_TIMEZONE = os.getenv("CRM_TIMEZONE", "UTC")
