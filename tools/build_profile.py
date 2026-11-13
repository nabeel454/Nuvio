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

import os
LOOPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loops')
def video(slug):
    return f'{base}/../loops/{slug}.mp4'.replace('/covers/../', '/') if os.path.exists(os.path.join(LOOPS, slug + '.mp4')) else None

def folder(slug, title, ids):
    return {'id': nid(slug), 'title': title, 'hideTitle': True,
            'coverImageUrl': f'{base}/{slug}.cover.jpg', 'customCoverImageUrl': f'{base}/{slug}.cover.jpg',
            'coverEmoji': None, 'focusGifUrl': None, 'focusGifEnabled': False,
            'defaultCoverSlug': None, 'heroBackdropUrl': f'{base}/{slug}.backdrop.jpg',
            'heroVideoUrl': video(slug), 'titleLogoUrl': None, 'coverSetId': None,
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

# ---------- 2b. Seasons collection ----------
seasons = [
    ('season-winter', 'Winter Comfort', ['genre_family_toprated_movies', 'genre_romantic_comedy_toprated_movies', 'studio_disney_animated_movies', 'anime_ghibli']),
    ('season-october', 'October Frights', ['themed_horror_classics_movies', 'themed_modern_horror_movies', 'kb_shudder_top50', 'genre_horror_movies']),
    ('season-spring', 'Spring Romance', ['genre_romance_toprated_movies', 'genre_romantic_comedy_movies', 'genre_romance_toprated_series']),
    ('season-summer', 'Summer Blockbusters', ['genre_action_toprated_movies', 'genre_adventure_toprated_movies', 'studio_marvel_movies', 'studio_lucasfilm_movies']),
]
seas = {'id': nid('collection/seasons'), 'title': 'Seasons', 'pinToTop': False,
        'focusGlowEnabled': True, 'viewMode': 'FOLLOW_LAYOUT', 'showAllTab': True,
        'backdropImageUrl': f'{base}/seasons.backdrop.jpg',
        'folders': [folder(sl, t, ids) for sl, t, ids in seasons]}
c['collections'] = [col for col in c['collections'] if col['id'] != seas['id']]
c['collections'].insert(2, seas)

# ---------- 2c. Matching covers for Genres / Directors / Decades (stock art kept as fallback) ----------
import re
def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
for title, prefix in [('Genres', 'genre-'), ('Directors', 'director-'), ('Decades', 'decade-')]:
    col = next(x for x in c['collections'] if x['title'] == title)
    for f in col['folders']:
        url = f'{base}/{prefix}{slugify(f["title"])}.cover.jpg'
        f['coverImageUrl'] = f['customCoverImageUrl'] = url
        f['heroBackdropUrl'] = url.replace('.cover.', '.backdrop.')
        f['hideTitle'] = True
        f['tileShape'] = 'LANDSCAPE'

# ---------- 2d. Friendlier collection names ----------
for col in c['collections']:
    col['title'] = {'Trending': "What Everyone's Watching", 'New & Latest': 'Fresh Releases',
                    'Canon & Best-Of': 'Best of the Best', 'Film Collections': 'Franchises',
                    'TV Collections': 'TV Universes'}.get(col['title'], col['title'])

# ---------- 2e. Settings: dedupe, hide watched, no shuffle on ranked rows ----------
c['home_dedupe'] = {'enabled': True}
c['filters']['exclude_watched'] = True
ranked = re.compile(r'top10|top50|top100|top20|top250|afi_|1001|awards_|trending|popular|snoak_|fp_|kb_|letterboxd')
for cid in list(c['catalog_overrides']):
    if ranked.search(cid) and c['catalog_overrides'][cid] == {'shuffle': 'daily'}:
        del c['catalog_overrides'][cid]

# ---------- 3. Home order: personal first, browse sections lower ----------
by_title = {col['title']: col['id'] for col in c['collections']}
order = ['Streaming', 'Tonight', 'Seasons', 'Recently Watched Movies', 'Recently Watched Series',
         "What Everyone's Watching", 'Fresh Releases', 'Studios', 'Franchises', 'TV Universes',
         'Directors', 'Awards', 'Best of the Best', 'Themes', 'Genres', 'World', 'Anime',
         'Anime Franchises', 'Decades', 'Runtime', 'Kids']
# Actors, Networks, Reality stay in the profile (browse) but leave the home screen
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
