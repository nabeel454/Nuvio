// Renders cover (1280x720) and backdrop (1920x1080) PNGs for each entry in covers.json.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const items = JSON.parse(fs.readFileSync(path.join(__dirname, 'covers.json'), 'utf8'));
const out = path.join(__dirname, '..', 'covers');

const motif = (m, c) => ({
  rank: `<text x="1180" y="700" font-family="Anton" font-size="900" fill="${c}" opacity=".16" text-anchor="end">10</text>`,
  rings: [0,1,2,3,4,5].map(i=>`<circle cx="1050" cy="250" r="${90+i*85}" fill="none" stroke="${c}" stroke-width="2" opacity="${.5-i*.07}"/>`).join(''),
  spot: `<defs><radialGradient id="s" cx=".72" cy="0" r=".9"><stop offset="0" stop-color="${c}" stop-opacity=".55"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient></defs><polygon points="760,0 1000,0 1280,720 420,720" fill="url(#s)"/>`,
  spiral: Array.from({length:14},(_,i)=>`<rect x="${1000-i*30}" y="${360-i*30}" width="${i*60}" height="${i*60}" fill="none" stroke="${c}" stroke-width="2" opacity="${.6-i*.035}" transform="rotate(${i*9} 1000 360)"/>`).join(''),
  frame: `<rect x="760" y="110" width="400" height="500" fill="none" stroke="${c}" stroke-width="3" opacity=".5"/><rect x="800" y="150" width="320" height="420" fill="${c}" opacity=".07"/>`,
  clock: `<circle cx="1030" cy="330" r="230" fill="none" stroke="${c}" stroke-width="3" opacity=".45"/><path d="M1030 330 L1030 100 A230 230 0 1 1 830 445 Z" fill="${c}" opacity=".14"/>`,
  laurel: Array.from({length:9},(_,i)=>`<ellipse cx="${1030+Math.cos((i/8)*Math.PI*0.9+0.3)*210}" cy="${380-Math.sin((i/8)*Math.PI*0.9+0.3)*210}" rx="16" ry="40" fill="${c}" opacity=".35" transform="rotate(${i*20-70} ${1030+Math.cos((i/8)*Math.PI*0.9+0.3)*210} ${380-Math.sin((i/8)*Math.PI*0.9+0.3)*210})"/>`).join(''),
  slash: [0,1,2].map(i=>`<polygon points="${820+i*140},0 ${900+i*140},0 ${640+i*140},720 ${560+i*140},720" fill="${c}" opacity="${.22-i*.06}"/>`).join(''),
  moon: `<circle cx="1040" cy="250" r="170" fill="${c}" opacity=".85"/><circle cx="1110" cy="210" r="160" fill="#0a0006"/>`,
  horizon: Array.from({length:9},(_,i)=>`<line x1="560" y1="${470+i*i*4}" x2="1280" y2="${470+i*i*4}" stroke="${c}" stroke-width="2" opacity="${.55-i*.05}"/>`).join('') + `<circle cx="960" cy="470" r="120" fill="${c}" opacity=".25"/>`,
}[m]);

const html = (it, w, h) => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Instrument+Serif:ital@0;1&family=Inter:wght@500;700&display=block" rel="stylesheet">
<style>
html,body{margin:0;width:${w}px;height:${h}px;overflow:hidden;background:${it.c2}}
.wrap{position:relative;width:1280px;height:720px;transform:scale(${w/1280});transform-origin:0 0;
 background:radial-gradient(120% 120% at 85% 10%, ${it.c1}33 0%, transparent 55%),linear-gradient(135deg, ${it.c2} 0%, #000 100%);}
svg{position:absolute;inset:0}
.grain{position:absolute;inset:0;opacity:.18;mix-blend-mode:overlay;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")}
.txt{position:absolute;left:84px;bottom:92px;color:#fff}
.k{font:700 22px/1 Inter;letter-spacing:.28em;text-transform:uppercase;color:${it.c1};margin-bottom:22px}
.t{font:400 150px/.9 'Instrument Serif';letter-spacing:-.02em}
.s{font:italic 400 150px/.9 'Instrument Serif';color:${it.c1};letter-spacing:-.02em}
.bar{position:absolute;left:84px;top:84px;width:56px;height:4px;background:${it.c1}}
</style></head><body><div class="wrap">
<svg viewBox="0 0 1280 720" width="1280" height="720">${motif(it.motif, it.c1)}</svg>
<div class="grain"></div><div class="bar"></div>
<div class="txt"><div class="k">${it.kicker}</div><div class="t">${it.title}</div>${it.sub?`<div class="s">${it.sub}</div>`:''}</div>
</div></body></html>`;

(async () => {
  const b = await chromium.launch();
  for (const [kind, w, h] of [['cover', 1280, 720], ['backdrop', 1920, 1080]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    for (const it of items) {
      await p.setContent(html(it, w, h), { waitUntil: 'networkidle' });
      await p.evaluate(() => document.fonts.ready);
      const file = path.join(out, `${it.slug}.${kind}.jpg`);
      await p.screenshot({ path: file, type: 'jpeg', quality: 88 });
    }
    await p.close();
  }
  await b.close();
  console.log('done');
})();
