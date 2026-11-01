"""Fetch uploaded Ballchasing replay details, retaining all available history."""
import json, os, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

TOKEN = os.environ.get('BALLCHASING_TOKEN')
if not TOKEN:
    raise SystemExit('BALLCHASING_TOKEN secret is missing')
BASE = 'https://ballchasing.com/api'
UPLOADER = '76561199012381219'
OUT = Path('stats.json')

def get(path, params=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'Authorization': TOKEN, 'User-Agent': 'EADC-stats/1.0'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f'Ballchasing API returned HTTP {exc.code} for {path}') from None

existing = {}
if OUT.exists():
    for item in json.loads(OUT.read_text()):
        if item.get('id'):
            existing[item['id']] = item
print('Previously saved replays:', len(existing))
cursor = None
ids = set()
for page in range(100):
    params = {'uploader': UPLOADER, 'count': 200, 'sort-by': 'replay-date', 'sort-dir': 'desc'}
    if cursor:
        params['after'] = cursor
    data = get('/replays', params)
    batch = data.get('list', [])
    if not batch:
        break
    ids.update(x['id'] for x in batch if x.get('id'))
    cursor = data.get('next')
    print('Scanned page', page+1, 'total replay IDs', len(ids))
    if not cursor:
        break
else:
    raise RuntimeError('Pagination exceeded 100 pages; increase limit before claiming complete history')

for i, rid in enumerate(ids - existing.keys(), 1):
    existing[rid] = get('/replays/' + urllib.parse.quote(rid, safe=''))
    if i % 10 == 0:
        print('Downloaded', i, 'new replay details')
    time.sleep(0.15)
OUT.write_text(json.dumps(list(existing.values()), separators=(',', ':')))
print('Saved', len(existing), 'replay details to stats.json')
