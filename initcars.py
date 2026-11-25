from db import db , client
from datacars import CARS

db.carmarket.delete_many({})
init = db.carmarket.insert_many(CARS)


print(db.carmarket.count_documents({}))
print(client.list_database_names())
test = list(db.carmarket.find({'city':'Lyon'}, {'_id':0, 'price':1))
total = 0
for p in test:
    
