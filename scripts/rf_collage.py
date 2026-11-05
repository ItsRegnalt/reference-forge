"""reference-forge: labelled progress collage (reference / output / difference columns, one row per view).

Run OUTSIDE Blender (needs Pillow):   python rf_collage.py spec.json out.png
spec.json:
{
  "title": "Magazine v3",
  "columns": [{"name": "Reference: Cinnamon M4A1"}, {"name": "Ours: Elwerici v3"}, {"name": "Difference"}],
  "rows": [
     {"label": "Right",  "images": ["ref_R.png", "mine_R.png", "diff_R.png"]},
     {"label": "Bottom", "images": ["ref_B.png", "mine_B.png", null]}
  ],
  "missing_label": "n/a",       (optional, text drawn in empty cells)
  "cell": 420                   (optional, cell size in px)
}
Optional per-column "note", top "subtitle" and bottom "footer" exist, but keep labels to what each image/model is.
Write labels in the user's language; a font with extended Latin glyphs is picked automatically.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont


def _font(size, bold=False):
    names = (['segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf', 'Arial Bold.ttf'] if bold
             else ['segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf', 'Arial.ttf'])
    dirs = [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'), '/usr/share/fonts/truetype/dejavu',
            '/usr/share/fonts/TTF', '/Library/Fonts', '/System/Library/Fonts/Supplemental', '/System/Library/Fonts']
    for d in dirs:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, width):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def collage(spec, out):
    cols, rows = spec['columns'], spec['rows']
    cell = int(spec.get('cell', 420)); pad = 10; lab_w = 120; missing = spec.get('missing_label', 'n/a')
    f_title, f_sub, f_col, f_note, f_row = _font(30, True), _font(18), _font(20, True), _font(15), _font(18, True)
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    note_lines = [_wrap(tmp, c.get('note', ''), f_note, cell - 2 * pad) for c in cols]
    head_h = 34 + max(len(l) for l in note_lines) * 20 + 10
    title_h = 50 + (28 if spec.get('subtitle') else 0)
    W = lab_w + len(cols) * (cell + pad) + pad
    foot = _wrap(tmp, spec.get('footer', ''), f_sub, W - 2 * pad) if spec.get('footer') else []
    H = title_h + head_h + len(rows) * (cell + pad) + pad + (len(foot) * 24 + 16 if foot else 0)
    img = Image.new('RGB', (W, H), (32, 33, 36)); d = ImageDraw.Draw(img)
    d.text((pad, 10), spec.get('title', ''), font=f_title, fill=(240, 240, 240))
    if spec.get('subtitle'):
        d.text((pad, 50), spec['subtitle'], font=f_sub, fill=(190, 200, 210))
    y0 = title_h
    for i, c in enumerate(cols):
        x = lab_w + i * (cell + pad)
        d.rectangle([x, y0, x + cell, y0 + head_h - 6], fill=(52, 56, 64))
        d.text((x + pad, y0 + 6), c['name'], font=f_col, fill=(255, 214, 120))
        for k, line in enumerate(note_lines[i]):
            d.text((x + pad, y0 + 34 + k * 20), line, font=f_note, fill=(205, 210, 215))
    y = y0 + head_h
    for r in rows:
        d.text((pad, y + cell // 2 - 12), r['label'], font=f_row, fill=(230, 230, 230))
        for i in range(len(cols)):
            x = lab_w + i * (cell + pad)
            p = r['images'][i] if i < len(r['images']) else None
            d.rectangle([x, y, x + cell, y + cell], fill=(46, 48, 52))
            if p and os.path.exists(p):
                im = Image.open(p).convert('RGBA'); im.thumbnail((cell, cell))
                bg = Image.new('RGBA', im.size, (46, 48, 52, 255)); bg.alpha_composite(im)
                img.paste(bg.convert('RGB'), (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
            else:
                tw = d.textlength(missing, font=f_note)
                d.text((x + (cell - tw) / 2, y + cell // 2 - 10), missing, font=f_note, fill=(150, 150, 150))
        y += cell + pad
    for k, line in enumerate(foot):
        d.text((pad, y + 6 + k * 24), line, font=f_sub, fill=(220, 220, 220))
    img.save(out)
    return out


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as fh:
        print(collage(json.load(fh), sys.argv[2]))
