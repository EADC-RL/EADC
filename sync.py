"""Sync EADC team replays from Ballchasing, keeping only the full trio."""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN = os.environ.get('BALLCHASING_TOKEN')
if not TOKEN:
    raise SystemExit('BALLCHASING_TOKEN secret is missing')

BASE = 'https://ballchasing.com/api'
UPLOADER = '76561199012381219'
OUT = Path('stats.json')
TEAM = {
    ('steam', '76561199012381219'),  # MAGIC
    ('steam', '76561198967865571'),  # Brotato
    ('epic', '68dd3104dcde490a81e250bcff91a69c'),  # Alleny / Dyslexic Donut
}


def get(path, params=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={'Authorization': TOKEN, 'User-Agent': 'EADC-stats/1.0'},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(
                f'Ballchasing API returned HTTP {exc.code} for {path}'
            ) from None


def full_team(replay):
    """Require all three IDs together on either blue or orange."""
    for side in ('blue', 'orange'):
        players = replay.get(side, {}).get('players', [])
        present = {
            (str(p.get('id', {}).get('platform', '')).lower(),
             str(p.get('id', {}).get('id', '')))
            for p in players
        }
        if TEAM.issubset(present):
            return True
    return False


existing = {}
if OUT.exists():
    for item in json.loads(OUT.read_text(encoding='utf-8')):
        if item.get('id') and full_team(item):
            existing[item['id']] = item
print('Previously saved qualifying EADC replays:', len(existing))

cursor = None
ids = set()
for page in range(100):
    params = {
        'uploader': UPLOADER,
        'count': 200,
        'sort-by': 'replay-date',
        'sort-dir': 'desc',
    }
    if cursor:
        params['after'] = cursor
    data = get('/replays', params)
    batch = data.get('list', [])
    if not batch:
        break
    ids.update(x['id'] for x in batch if x.get('id'))
    cursor = data.get('next')
    print('Scanned page', page + 1, 'total replay IDs', len(ids))
    if not cursor:
        break
else:
    raise RuntimeError('Pagination exceeded 100 pages; increase limit')

new_ids = sorted(ids - existing.keys())
for i, rid in enumerate(new_ids, 1):
    replay = get('/replays/' + urllib.parse.quote(rid, safe=''))
    if full_team(replay):
        existing[rid] = replay
    if i % 10 == 0:
        print('Checked', i, 'replays for full EADC team')
    time.sleep(0.15)

# Stable chronological ordering also makes match-history views predictable.
qualified = sorted(existing.values(), key=lambda r: (r.get('date', ''), r.get('id', '')))
OUT.write_text(json.dumps(qualified, separators=(',', ':')), encoding='utf-8')
print('Excluded', len(ids) - len(existing), 'non-EADC replay IDs from scanned uploads')
print('Saved', len(qualified), 'qualifying EADC replay details to stats.json')
