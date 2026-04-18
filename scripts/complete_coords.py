import json, pathlib

rows=json.loads(pathlib.Path('places_geocoded_final.json').read_text(encoding='utf-8'))
by_place={r['place']: r for r in rows}

def set_place(place, lat, lon, display_name, method, notes=None):
    r=by_place[place]
    r['lat']=float(lat)
    r['lon']=float(lon)
    r['display_name']=display_name
    r['method']=method
    if notes:
        r['notes']=notes

# From Overpass (recorded in console output)
set_place('Black Dragon Canyon petroglyphs', 38.9429094, -110.4242049,
          'Black Dragon Pictographs (OSM)', 'overpass',
          'Mapped in OSM as "Black Dragon Pictographs".')
set_place('Buckhorn Wash petroglyphs', 39.1234513, -110.694057,
          'Buckhorn Draw Pictograph Panel (OSM)', 'overpass',
          'Mapped in OSM as "Buckhorn Draw Pictograph Panel"; used as proxy for Buckhorn Wash petroglyphs corridor.')
set_place('Loan Warrior Petroglyph', 38.8534311, -110.8036853,
          'Lone Warrior Pictograph (OSM)', 'overpass',
          'Trip text says "Loan Warrior"; OSM has "Lone Warrior Pictograph".')
set_place('Circa Loan Warrior petroglyph', 38.8534311, -110.8036853,
          'Lone Warrior Pictograph (OSM)', 'derived',
          'Used same coordinates as Lone Warrior Pictograph.')

# Derived from already geocoded nearby items
# Temple Wash Petroglyphs -> Temple Mountain Wash Pictograph Panel (already in file)
tmw=by_place.get('Temple Mountain Wash')
if tmw and tmw.get('lat') is not None:
    set_place('Temple Wash Petroglyphs', tmw['lat'], tmw['lon'],
              'Temple Mountain Wash Pictograph Panel (proxy)', 'derived',
              'Trip label likely refers to petroglyph/pictograph panel in Temple Mountain Wash; used that known panel location.')

# North Temple Mountain Wash -> use North Temple Wash
ntw=by_place.get('North Temple Wash')
if ntw and ntw.get('lat') is not None:
    set_place('North Temple Mountain Wash', ntw['lat'], ntw['lon'],
              'North Temple Wash (proxy)', 'derived',
              'Used North Temple Wash coordinates (closest named wash in dataset).')

# The Wedge (San Rafael Swell) -> use Wedge Overlook
wo=by_place.get('Wedge Overlook')
if wo and wo.get('lat') is not None:
    set_place('The Wedge (San Rafael Swell)', wo['lat'], wo['lon'],
              'Wedge Overlook (proxy)', 'derived',
              'Used Wedge Overlook coordinates.')

# Head of Sinbad / Sinbad\'s Head: prefer OSM node "Head of Sinbad" at 38.8754842,-110.766174 (closer to I-70)
set_place('Head of Sinbad', 38.8754842, -110.766174,
          'Head of Sinbad (OSM locality)', 'overpass')
set_place("Sinbad's Head", 38.8754842, -110.766174,
          'Head of Sinbad (OSM locality)', 'derived',
          'Used same coordinates as Head of Sinbad.')

# Eagle Canyon Bridges: choose I-70 bridge segments in Eagle Canyon area (OSM: I 70 bridge=yes)
# Using center of way 32081162 (bridge=yes) from Overpass: 38.8598386,-110.8649906
set_place('Eagle Canyon Bridges', 38.8598386, -110.8649906,
          'I-70 bridge segments near Eagle Canyon (OSM)', 'overpass',
          'Approximate: I-70 bridge=yes segments in Eagle Canyon area. Represents the under/overpass â€œCanyon Bridgesâ€.')

# Old San Rafael Swinging Bridge: Overpass lookup kept timing out.
# Approximate using Buckhorn Draw corridor: place near Buckhorn Draw Pictograph Panel (close to river corridor).
# Set to Buckhorn Draw Pictograph Panel as a reasonable corridor proxy until refined.
set_place('Old San Rafael Swinging Bridge', 39.1234513, -110.694057,
          'Buckhorn Draw corridor (approx; needs refinement)', 'approx',
          'Overpass bridge search timed out; set to Buckhorn Draw corridor (near river corridor). If you want, we can refine later by searching a known â€œSwinging Bridgeâ€ POI source.')

# sanity: ensure all have coords
missing=[p for p,r in by_place.items() if r.get('lat') is None]
print('still missing:', missing)

out=list(by_place.values())
pathlib.Path('places_geocoded_complete.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print('wrote places_geocoded_complete.json with', len(out), 'rows')
