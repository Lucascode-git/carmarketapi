import sys
import requests

BASE = 'http://127.0.0.1:5001/api/v1.0'
results = []

def check(name, r, expected):
    ok = r.status_code == expected
    results.append(ok)
    status = 'OK  ' if ok else 'FAIL'
    print(f'{status} {name} (attendu {expected}, reçu {r.status_code})')
    return ok

# Adapte ces champs à ceux que ta route POST exige
NEW_CAR = {'brand': 'Fiat', 'model': 'Panda', 'year': 2019,
           'price': 8500, 'city': 'Lyon', 'fuel': 'Petrol', 'mileage_km': 60000}

# GET
check('GET liste', requests.get(f'{BASE}/cars'), 200)
check('GET page trop loin', requests.get(f'{BASE}/cars', params={'page': 999}), 404)
check('GET page invalide', requests.get(f'{BASE}/cars', params={'page': 'abc'}), 400)
check('GET stats', requests.get(f'{BASE}/stats'), 200)

# POST
r = requests.post(f'{BASE}/cars', json=NEW_CAR)
if not check('POST valide', r, 201):
    sys.exit('POST a échoué : impossible de tester la suite')
car_id = r.json()['id']   # adapte si ton POST renvoie l'id ailleurs
check('POST incomplet', requests.post(f'{BASE}/cars', json={'brand': 'Fiat'}), 400)
check('POST pas en JSON', requests.post(f'{BASE}/cars', data='brand=Fiat'), 400)

# PATCH
url = f'{BASE}/cars/{car_id}'
check('PATCH prix', requests.patch(url, json={'price': 9000}), 200)
check('PATCH champ interdit', requests.patch(url, json={'id': 99}), 400)
check('PATCH vide', requests.patch(url, json={}), 400)
check('PATCH annonce inconnue', requests.patch(f'{BASE}/cars/999999', json={'price': 1}), 404)

# PUT
check('PUT complet', requests.put(url, json=NEW_CAR), 200)
check('PUT annonce inconnue', requests.put(f'{BASE}/cars/999999', json=NEW_CAR), 404)

# DELETE : supprime aussi l'annonce de test, ta base reste propre
check('DELETE', requests.delete(url), 200)
check('DELETE une seconde fois', requests.delete(url), 404)

print(f'\n{sum(results)}/{len(results)} OK')