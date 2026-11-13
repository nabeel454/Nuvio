# Nuvio – curated Xperience home

- `covers/` – custom cover (1280×720) and hero backdrop (1920×1080) art
- `tools/covers.json` + `tools/render_covers.js` – edit text/colours and re-render (`node tools/render_covers.js`)
- `tools/build_profile.py` – turns an Xperience profile export into the curated layout:
  `python3 tools/build_profile.py export.json curated.json <public-image-base-url>`

Streaming folders keep their original Xperience artwork; only their row order changes
(Top 10 → Latest → Originals → Top rated → All → Kids), plus two new folders up front.
