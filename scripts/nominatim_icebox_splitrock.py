import json, urllib.parse, urllib.request
UA='SanRafaelSwellPlanner/1.0'

def nom(q):
    url='https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q':q,'format':'jsonv2','limit':3})
    req=urllib.request.Request(url, headers={'User-Agent':UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data=json.loads(resp.read().decode('utf-8'))
    print('\nQ:',q,'results',len(data))
    for d in data:
        print('-',d.get('lat'),d.get('lon'),'|',d.get('display_name'))

for q in [
    'The Icebox, San Rafael Swell, Utah',
    'Icebox Canyon, San Rafael Swell, Utah',
    'Icebox, Eagle Canyon, Utah',
    'Split Rock, San Rafael Swell, Utah',
    'Split Rock, Buckhorn Wash, Utah',
    'Split Rock, Emery County, Utah',
    'Split Rock, San Rafael River, Utah',
]:
    try:
        nom(q)
    except Exception as e:
        print('\nQ:',q,'ERROR',e)
