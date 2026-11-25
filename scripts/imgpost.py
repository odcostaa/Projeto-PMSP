import json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
D = 'site/img'
d = json.load(open('site/questoes.json'))
PAD = 8

def lum(a): return (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114)
def trim(im, pad=PAD):
    a = np.asarray(im.convert('RGB')).astype(int)
    m = lum(a) < 244
    if not m.any(): return im
    ys, xs = np.where(m)
    x0, x1, y0, y1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, im.width), max(ys.min() - pad, 0), min(ys.max() + pad + 1, im.height)
    return im.crop((x0, y0, x1, y1))
def photo(im):
    a = lum(np.asarray(im.convert('RGB')).astype(float))
    return (((a > 40) & (a < 215)).mean()) > 0.12
def alpha_white(im):
    a = np.asarray(im.convert('RGB')).astype(float)
    al = 255 - a.min(axis=2)               # tinta = quanto menos branco
    al = np.clip((al - 30) * 255 / 225, 0, 255)
    k = np.maximum(al, 1)[..., None] / 255
    col = np.clip(255 - (255 - a) / k, 0, 255)
    col[al == 0] = 0
    out = np.dstack([col, al]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')
def drop_label(im):
    a = lum(np.asarray(im.convert('RGB')).astype(float)); m = a < 150
    h = ndi.binary_dilation(m[:40], structure=np.ones((3, 9)))
    lab, n = ndi.label(h)
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        y, x = sl
        if y.start < 22 and (y.stop - y.start) < 28 and (x.stop - x.start) < 70 and x.start < 0.45 * im.width:
            im.paste((255, 255, 255), (max(x.start - 3, 0), 0, x.stop + 3, min(y.stop + 4, 40)))
    return im
def save(im, base):
    ph = photo(im); name = base + ('-f' if ph else '') + '.png'
    (im.convert('RGB') if ph else alpha_white(im)).save(os.path.join(D, name), optimize=True)
    return 'img/' + name
mp = {}
def proc(path):
    if path in mp: return mp[path]
    im = trim(Image.open('site/' + path).convert('RGB'))
    mp[path] = save(im, os.path.splitext(os.path.basename(path))[0] + '_t')
    return mp[path]
L5 = 'ABCDE'
for q in d:
    for k in ('figuras', 'figuras_q'):
        if q.get(k): q[k] = [proc(u) for u in q[k]]
    for b in q.get('blocos') or []:
        if 'i' in b: b['i'] = proc(b['i'])
    m = q.get('imgq')
    if m:
        if m['altimg']:
            im = Image.open('site/' + m['f']).convert('RGB'); m['altf'] = {}
            for i, l in enumerate(L5):
                y0 = m['alts'][l] - 6; y1 = (m['alts'][L5[i + 1]] - 6) if i < 4 else m['h']
                seg = drop_label(im.crop((0, max(y0, 0), im.width, min(y1, im.height))).copy())
                m['altf'][l] = save(trim(seg), f"{q['id']}_a{l}")
        else: q.pop('imgq')
json.dump(d, open('site/questoes.json', 'w'), ensure_ascii=False)
ref = {'img/' + f for f in []}
for q in d:
    for k in ('figuras', 'figuras_q'): ref.update(q.get(k) or [])
    for b in q.get('blocos') or []:
        if 'i' in b: ref.add(b['i'])
    for v in ((q.get('imgq') or {}).get('altf') or {}).values(): ref.add(v)
for f in os.listdir(D):
    if 'img/' + f not in ref: os.remove(os.path.join(D, f))
json.dump(['questoes.json'] + sorted(ref), open('work/files.json', 'w'))
print('imagens', len(ref), 'fotos', sum(1 for r in ref if r.endswith('-f.png')))
