import os
import certifi
from dotenv import load_dotenv
import pymongo

load_dotenv()
KEY = os.getenv('MONGOKEY')

URL = f'mongodb+srv://lf16code_db_user:{KEY}@30daysofpython.ozjjgep.mongodb.net/'

client = pymongo.MongoClient(URL, tlsCAFile=certifi.where())

db = client['carmarket']
