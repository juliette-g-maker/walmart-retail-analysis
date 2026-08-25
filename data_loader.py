import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd

# Charge les variables du fichier .env (dont DATABASE_URL)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_engine():
    return create_engine(DATABASE_URL)

def load_data():
    engine = get_engine()
    stores = pd.read_sql("SELECT * FROM stores", engine)
    features = pd.read_sql("SELECT * FROM features", engine)
    sales = pd.read_sql("SELECT * FROM sales", engine)
    return stores, features, sales
    