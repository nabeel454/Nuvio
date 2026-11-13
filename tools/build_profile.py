"""Build a polished Xperience profile from an exported one.

Usage: python3 build_profile.py <input.json> <output.json> <image_base_url>
Only uses catalog IDs that already exist in the input profile.
"""
import json, sys, uuid, copy

src, dst, base = sys.argv[1], sys.argv[2], sys.argv[3].rstrip('/')
prof = json.load(open(src))
c = prof['config']
ADDON = 'app.xperience.b1a56536-7a8b-4f1c-8ebe-5145210a7d5d'

known = {}  # catalogId -> type
for col in c['collections']:
    for f in col['folders']:
        for s in f['catalogSources']:
            known[s['catalogId']] = s['type']
def typ(cid):
    if cid in known: return known[cid]
    return 'series' if cid.endswith('series') or 'shows' in cid else 'movie'
valid = set(known) | set(c['catalog_overrides']) | {r['catalog_id'] for r in c['home_rows']}

def sources(ids):
    out = []
    for i in ids:
        if i not in valid:
            print('  skip unknown catalog', i); continue
        out.append({'addonId': ADDON, 'type': typ(i), 'catalogId': i, 'genre': None})
    return out

def nid(name):  # stable ids so re-running doesn't create duplicates
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'nuvio-custom/' + name))

def folder(slug, title, ids):
    return {'id': nid(slug), 'title': title, 'hideTitle': True,
            'coverImageUrl': None, 'customCoverImageUrl': f'{base}/{slug}.cover.jpg',
            'coverEmoji': None, 'focusGifUrl': None, 'focusGifEnabled': False,
            'defaultCoverSlug': None, 'heroBackdropUrl': f'{base}/{slug}.backdrop.jpg',
            'heroVideoUrl': None, 'titleLogoUrl': None, 'coverSetId': None,
            'backdropSetId': None, 'tileShape': 'LANDSCAPE', 'catalogSources': sources(ids)}

# ---------- 1. Streaming: keep every folder + its artwork, re-order sources ----------
def rank(cid):
    if 'kids' in cid: return (9, cid.endswith('series'))
    for n, key in enumerate(['top10', 'top50', 'latest', 'originals', 'toprated', 'uk_', 'kids']):
        if key in cid: return (n if key != 'kids' else 9, cid.endswith('series'))
    return (6, cid.endswith('series'))
stream = next(col for col in c['collections'] if col['title'] == 'Streaming')
for f in stream['folders']:
    f['catalogSources'].sort(key=lambda s: rank(s['catalogId']))

allids = sorted(valid)
top10 = [i for i in allids if ('top10' in i or 'top50' in i) and ('snoak_' in i or 'fp_' in i or 'kb_' in i) and 'kids' not in i]
latest = [i for i in allids if i.startswith('snoak_latest_') or (i.startswith('streaming_') and '_latest_' in i)]
stream['folders'] = [folder('top10-everywhere', 'Top 10 Everywhere', top10),
                     folder('new-on-streaming', 'Just Landed', latest)] + \
                    [f for f in stream['folders'] if f['title'] not in ('Top 10 Everywhere', 'Just Landed')]

# ---------- 2. New curated collection ----------
curated = [
    ('mind-benders', 'Mind Benders', ['themed_mindfuck', 'themed_plot_twists', 'themed_time_loop', 'themed_time_travel', 'themed_time_travel_series']),
    ('arthouse-nights', 'Arthouse Nights', ['studio_a24_movies', 'streaming_mubi_toprated_movies', 'awards_criterion', 'streaming_mubi_latest_movies', 'studio_a24_series']),
    ('edge-of-your-seat', 'Edge of Your Seat', ['genre_thriller_toprated_movies', 'themed_heists', 'themed_whodunnit', 'themed_serial_killer', 'themed_heist_series']),
    ('after-midnight', 'After Midnight', ['themed_modern_horror_movies', 'themed_horror_classics_movies', 'kb_shudder_top50', 'genre_horror_toprated_movies']),
    ('under-90', 'Under 90 Minutes', ['runtime_short_movies']),
    ('epic-night-in', 'Epic Night In', ['runtime_epic_movies', 'runtime_long_movies']),
    ('the-canon', 'The Canon', ['awards_letterboxd_top250', 'awards_imdb_top250_movies', 'awards_afi_top100', 'awards_1001_movies', 'awards_imdb_top250_series']),
]
tonight = {'id': nid('collection/tonight'), 'title': 'Tonight', 'pinToTop': True,
           'focusGlowEnabled': True, 'viewMode': 'FOLLOW_LAYOUT', 'showAllTab': True,
           'backdropImageUrl': f'{base}/tonight.backdrop.jpg',
           'folders': [folder(s, t, ids) for s, t, ids in curated]}
c['collections'] = [col for col in c['collections'] if col['id'] != tonight['id']]
c['collections'].insert(1, tonight)

# ---------- 3. Home order: personal first, browse sections lower ----------
by_title = {col['title']: col['id'] for col in c['collections']}
order = ['Streaming', 'Tonight', 'Recently Watched Movies', 'Recently Watched Series', 'Trending',
         'New & Latest', 'Studios', 'Film Collections', 'TV Collections', 'Directors', 'Awards',
         'Canon & Best-Of', 'Themes', 'Genres', 'World', 'Anime', 'Anime Franchises', 'Decades',
         'Runtime', 'Networks', 'Actors', 'Kids', 'Reality']
order += [t for t in by_title if t not in order]
keep_rows = ['recs_movies_for_you']  # the rest are already inside collections
c['home_order'] = [{'kind': 'catalog', 'id': r} for r in keep_rows] + \
                  [{'kind': 'collection', 'id': by_title[t]} for t in order]
for r in c['home_rows']:
    r['enabled'] = r['catalog_id'] in keep_rows
c['home_rows'].sort(key=lambda r: (not r['enabled'], r['position']))
for n, r in enumerate(c['home_rows']): r['position'] = n

prof['name'] = prof.get('name', 'Profile') + ' – Curated'
json.dump(prof, open(dst, 'w'), indent=1, ensure_ascii=False)
print('collections', len(c['collections']), '| home blocks', len(c['home_order']))
for f in tonight['folders'] + stream['folders'][:2]:
    print(f"  {f['title']}: {[s['catalogId'] for s in f['catalogSources']]}")
