"""Verify HTML deliverables + GPX parseability."""
from __future__ import annotations
import pathlib
import re
import xml.etree.ElementTree as ET

BASE = pathlib.Path(__file__).resolve().parent.parent

def check_html(path):
    p = pathlib.Path(path)
    txt = p.read_text(encoding='utf-8')
    n = len(txt)
    issues = []

    # Simple balance check: every <div ...> should match a </div>
    opens = len(re.findall(r'<div\b', txt))
    closes = len(re.findall(r'</div>', txt))
    if opens != closes:
        issues.append(f'<div> imbalance: {opens} opens, {closes} closes')

    # No unclosed script tag
    script_opens = len(re.findall(r'<script\b', txt))
    script_closes = len(re.findall(r'</script>', txt))
    if script_opens != script_closes:
        issues.append(f'<script> imbalance: {script_opens} vs {script_closes}')

    # Check CSS opens/closes roughly balanced
    if txt.count('{') != txt.count('}'):
        issues.append(f'brace imbalance: {{={txt.count("{")} }}={txt.count("}")}')

    # Check that there are tabs/panes
    tabs = len(re.findall(r'class="tab-btn', txt))
    panes = len(re.findall(r'class="tab-pane', txt))
    if tabs or panes:
        print(f'  tabs={tabs}, panes={panes}')

    print(f'{p.name}: {n/1024:.1f} KB, {"OK" if not issues else "ISSUES: " + "; ".join(issues)}')
    return not issues

def check_gpx(path):
    p = pathlib.Path(path)
    tree = ET.parse(p)
    root = tree.getroot()
    ns = {'g': 'http://www.topografix.com/GPX/1/1'}
    wpts = root.findall('g:wpt', ns)
    trks = root.findall('g:trk', ns)
    trk_info = []
    for t in trks:
        nm = t.findtext('g:name', default='(unnamed)', namespaces=ns)
        pts = t.findall('g:trkseg/g:trkpt', ns)
        trk_info.append((nm, len(pts)))
    camp_backups = sum(1 for w in wpts if '[CAMP BACKUP]' in (w.findtext('g:name', default='', namespaces=ns) or ''))
    camp_primary = sum(1 for w in wpts if '[CAMP PRIMARY]' in (w.findtext('g:name', default='', namespaces=ns) or ''))
    camp_last = sum(1 for w in wpts if '[CAMP LAST-RESORT]' in (w.findtext('g:name', default='', namespaces=ns) or ''))
    hike_wpts = sum(1 for w in wpts if '[HIKE]' in (w.findtext('g:name', default='', namespaces=ns) or ''))
    backup_pois = sum(1 for w in wpts if re.match(r'^\[BACKUP\]', w.findtext('g:name', default='', namespaces=ns) or ''))
    print(f'{p.name}: {p.stat().st_size/1024:.1f} KB')
    print(f'  waypoints: {len(wpts)}')
    print(f'    primary camps: {camp_primary}')
    print(f'    backup camps: {camp_backups}')
    print(f'    last-resort camps: {camp_last}')
    print(f'    hike candidates: {hike_wpts}')
    print(f'    backup POIs: {backup_pois}')
    print(f'    primary POIs: {len(wpts) - camp_primary - camp_backups - camp_last - hike_wpts - backup_pois}')
    print(f'  tracks: {len(trks)}')
    for nm, n in trk_info:
        print(f'    [{n:5d} pts] {nm}')
    return True


def main():
    check_html(BASE / 'trip-itinerary.html')
    check_html(BASE / 'trip-reference.html')
    check_html(BASE / 'slot-canyon-guide.html')
    check_html(BASE / 'fuel-plan.html')
    check_gpx(BASE / 'trip-plan.gpx')


if __name__ == '__main__':
    main()
