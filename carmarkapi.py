
from flask import Flask, request, abort, url_for
from werkzeug.exceptions import HTTPException
from db import db 
from pymongo import ReturnDocument
import datetime
import statistics



app = Flask(__name__)
app.json.sort_keys = False

API = '/api/v1.0'

# FILTERS -----------------------------------------------
@app.errorhandler(HTTPException)
def errors_mess(e):
    return {'error': e.name, 'message': e.description}, e.code


# FUNCTIONS ---------------------------------------------
# 1______________
def filters(city='', fuel='', max_price='', max_km='', min_year=''):
    query = {}
    if city:
        query['city'] = city
    if fuel:
        query['fuel'] = fuel
    if max_price:
        query['max_price'] = {'$lte': max_price}
    if max_km:
        query['max_km'] = {'$lte': max_km}
    if min_year:
        query['min_year'] = {'$gte': max_km}
    return query
 
def testnum(num):
    test = request.args.get(num, '').strip()
    if test == '':
        return None
    try:
        nb = int(test)
    except ValueError:
        abort(400, description=f'Enter a valid number, input: {num}')
    if nb < 0:
        abort(400, description=f'Enter a positiv number, input: {num}')
    return nb
# _______________
# 4______________
def read_json():
    ask = request.get_json(silent=True)
    if not isinstance(ask, dict):
        abort(400, description=f'Must be JSON')
    return ask 

FUELS = ['Diesel', 'Electric', 'Hybrid', 'Petrol']
EDITABLE = ['brand', 'model', 'city', 'year', 'price', 'mileage_km', 'fuel']

def make_errors(data, required):
    errors = []
    for field in sorted(required - set(data)):
        errors.append(f'{field}: required')
    for field, value in data.items():
        if field not in EDITABLE:
            errors.append(f'{field} NOT EDITABLE')
        elif field in ('brand', 'model', 'city'):
            if not isinstance(value, str) or value.strip() == '':
                errors.append(f'{field}: non-empty text is required')
        elif field == 'year':
            if type(value) is not int or value < 1990 or value > 2027:
                errors.append(f'{field}: must be a year in NUMBER between 1990-2027')
        elif field == 'price':
            if type(value) is not int or value < 1:
                errors.append(f'{field}: positive number only')
        elif field == 'mileage_km':
            if type(value) is not int or value <= -1:
                errors.append(f'{field}: no negative number')
        elif field == 'fuel':
            if value.title() not in FUELS or type(value) is not str:
                errors.append(f'{field}: not a valid fuel')
    return errors

def to_json(value):
    value.pop('_id',None)
    return value
    



# ROUTES ------------------------------------------------
# 1______________
@app.route(f'{API}/cars', methods=['GET'])
def list_cars():
    city = request.args.get('city', '')
    fuel = request.args.get('fuel', '')
    max_price = testnum('max_price')
    max_km = testnum('max_km')
    min_year = testnum('min_year')

    query = filters(city.title(), fuel.title(), max_price, max_km, min_year)
    total = db.carmarket.count_documents(query)

    BYPAGE = 10
    page = testnum('page') or 1
    pages = max(1, -(-total // BYPAGE))
    if page > pages:
        abort(404, description=f"Page {page} doesn't exist, last page {pages}")
    result = list(db.carmarket.find(query, {'_id':0, 'id':1, 'brand':1, 'model':1, 'year':1, 'price':1, 'city':1}).sort({'price':1, 'id':1}).skip((page - 1) * BYPAGE).limit(BYPAGE))
    
    return {'count':total, 'page':page, 'pages':pages, 'results':result}
    
# 2______________
@app.route(f'{API}/cars/<int:car_id>', methods=['GET'])
def one_car(car_id):
    result = db.carmarket.find_one({'id':car_id}, {'_id':0})
    if not result:
        abort(404)
    date = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    result['created_at'] =  date
    return result
    
# 3_______________
@app.route(f'{API}/stats', methods=['GET'])
def stats():
    prices = [car['price'] for car in db.carmarket.find({}, {'_id': 0, 'price': 1})]
    if not prices:
        abort(404, description='No car in the database')
    return {
        'count': len(prices),
        'fuels': sorted(db.carmarket.distinct('fuel')),
        'cities': sorted(db.carmarket.distinct('city')),
        'average_price': round(statistics.mean(prices)),
    }

# 4_______________
@app.route(f'{API}/cars', methods=['POST'])
def get_post():
    data = read_json()
    errors = make_errors(data, set(EDITABLE))
    if errors:
        return {'error': 'Bad Request', 'messages': errors}, 400
    last = db.carmarket.find_one({}, sort=[('id',-1)])
    car = {
        'id': last['id']+1 if last else 1,
        'slug': f'{data['brand'].strip()}-{data['model'].strip()}',
        'created_at': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    }
    return to_json(car), 201, {'Location':url_for('one_car', car_id=car['id'])}


# 5________________
@app.route(f'{API}/cars/<int:car_id>', methods=['PUT'])
def get_put(car_id):
    data = read_json()
    errors = make_errors(data, set(EDITABLE))
    if errors:
        return {'error': 'Bad Request', 'message':errors}, 400
    old = db.carmarket.find_one({'id':car_id})
    if old is None:
        abort(404, description=f'No car with id: {car_id}')
    new = {
        'slug': f'{data['brand'].strip()}-{data['model'].strip()}',
        'brand': data['brand'].strip(),
        'model':data['model'].strip(),
        'city':data['city'].title().strip(),
        'year':int(data['year']),
        'price':int(data['price']),
        'mileage_km': int(data['mileage_km']),
        'fuel':data['fuel'].title()
    }
    if 'id' in old:
        new['id'] = old['id']
    if 'created_at' in old:
        new['created_at'] = old['created_at']
    db.carmarket.replace_one({'id': car_id}, new)
    return to_json(new)


# 6________________
@app.route(f'{API}/cars/<int:car_id>', methods=['PATCH'])
def get_patch(car_id):
    data = read_json()
    if not data:
        abort(400, description='Nothing to update')
    errors = make_errors(data, required=set())
    if errors:
        return {'error':'Bad Request', 'message': errors}, 400
    car = db.carmarket.find_one_and_update({'id':car_id}, {'$set': data}, return_document=ReturnDocument.AFTER)
    if car is None:
        abort(404, description=f'No book with id: {car_id}')
    return to_json(car)


# 7_________________
@app.route(f'{API}/cars/<int:car_id>', methods=['DELETE'])
def get_delete(car_id):
    result = db.carmarket.delete_one({'id':car_id})
    if result.deleted_count == 0:
        abort(404, description=f'No car with id: {car_id} to delete')
    return '', 204
