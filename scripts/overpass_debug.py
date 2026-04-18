import urllib.request

overpass='https://overpass.kumi.systems/api/interpreter'
query='''[out:json][timeout:60];
node["name"~"San Rafael",i](38.5,-111.3,39.3,-110.0);
out;'''
req=urllib.request.Request(overpass, data=query.encode('utf-8'), headers={'User-Agent':'SanRafaelSwellPlanner/1.0'})
with urllib.request.urlopen(req, timeout=120) as resp:
    body=resp.read()
    print('status', resp.status, resp.headers.get('content-type'))
    print(body[:400])
