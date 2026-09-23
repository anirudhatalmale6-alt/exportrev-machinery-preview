# -*- coding: utf-8 -*-
"""Turn a real stock file into the site's inventory.

This is the bridge between "we have a lot of machines" and a live marketplace.
Fill in stock-template.csv (or export the same columns from Excel) and run:

    python3 import_stock.py stock.csv        -> assets/data.js
    python3 import_stock.py stock.xlsx       -> assets/data.js

After that the site shows YOUR machines instead of the demonstration ones, and
nothing else has to change: the filters, the categories, the masonry and the
detail sheet all read from the same file.

What it does for you, so the listing cannot quietly go wrong:

  * refuses a row with no make, model or price, and says which line;
  * warns when a category is not one the site knows, instead of silently
    dropping the machine out of every filter;
  * picks the right silhouette from the category;
  * keeps a photo only if the file is actually on disk;
  * reports what it did — how many rows in, how many published, what it skipped.
"""

import csv
import io
import json
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

# The categories the site draws silhouettes and filters for.
FORMES = {
    'Trucks and heavy vehicles': 'truck',
    'Excavators': 'excavator',
    'Loaders': 'loader',
    'Cranes': 'crane',
    'Bulldozers': 'dozer',
    'Dumpers and haulers': 'dumper',
    'Concrete equipment': 'mixer',
    'Material handling': 'forklift',
    'Road construction equipment': 'roller',
    'Drilling machinery': 'drill',
    'Mining equipment': 'mining',
    'Industrial equipment': 'industrial',
    'Spare parts': 'parts',
}

COLONNES = ['reference', 'category', 'make', 'model', 'year', 'price',
            'hours', 'weight_t', 'power_hp', 'city', 'country', 'status',
            'photo', 'photo_credit', 'photo_licence', 'photo_source']

HUES = [96, 104, 112, 120, 128, 136, 144, 88]
ETATS_OK = ('Available', 'Under offer', 'Just listed', 'Sold')


def nombre(v, defaut=0):
    """Accept 1 250 000, 1,250,000, '1.250.000 EUR', 12 500.50 — all of it."""
    if v is None:
        return defaut
    s = str(v).strip()
    if not s:
        return defaut
    s = re.sub(r'[^\d.,-]', '', s)
    if s.count(',') and s.count('.'):
        s = s.replace(',', '') if s.rfind('.') > s.rfind(',') else s.replace('.', '').replace(',', '.')
    elif s.count(','):
        # a single comma is a decimal separator only if 1-2 digits follow it
        s = s.replace(',', '.') if re.search(r',\d{1,2}$', s) else s.replace(',', '')
    try:
        return float(s)
    except ValueError:
        return defaut


def lignes(chemin):
    if chemin.lower().endswith(('.xlsx', '.xlsm')):
        import openpyxl
        wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        entete = [str(c or '').strip().lower() for c in next(it)]
        for r in it:
            yield dict(zip(entete, r))
    else:
        with io.open(chemin, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                yield {(k or '').strip().lower(): v for k, v in row.items()}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    chemin = sys.argv[1]
    if not os.path.exists(chemin):
        print('File not found: %s' % chemin)
        return 2

    machines, ignores, alertes = [], [], []
    for n, row in enumerate(lignes(chemin), start=2):   # row 1 is the header
        marque = (row.get('make') or '').strip()
        modele = (row.get('model') or '').strip()
        prix = int(nombre(row.get('price')))
        if not marque or not modele:
            ignores.append('line %d: no make or model' % n)
            continue
        if prix <= 0:
            ignores.append('line %d: %s %s has no price' % (n, marque, modele))
            continue

        cat = (row.get('category') or '').strip()
        if cat not in FORMES:
            proche = [c for c in FORMES if c.lower().startswith(cat.lower()[:4])] if cat else []
            alertes.append('line %d: category %r is not one the site knows%s'
                           % (n, cat, (' — did you mean %r?' % proche[0]) if proche else ''))

        etat = (row.get('status') or 'Available').strip() or 'Available'
        if etat not in ETATS_OK:
            alertes.append('line %d: status %r — using Available' % (n, etat))
            etat = 'Available'

        ref = (row.get('reference') or '').strip() or 'ER-%04d' % (1000 + len(machines))
        photo = (row.get('photo') or '').strip()
        if photo:
            sur_disque = os.path.join(ICI, photo.lstrip('/'))
            if not os.path.exists(sur_disque):
                alertes.append('line %d: photo %r is not on disk — keeping the drawing' % (n, photo))
                photo = ''

        m = {
            'ref': ref,
            'cat': cat,
            'mfr': marque,
            'model': modele,
            'year': int(nombre(row.get('year'))) or 0,
            'price': prix,
            'hours': int(nombre(row.get('hours'))),
            'weight': round(nombre(row.get('weight_t')), 1),
            'power': int(nombre(row.get('power_hp'))),
            'city': (row.get('city') or '').strip(),
            'country': (row.get('country') or '').strip(),
            'status': etat,
            'hue': HUES[len(machines) % len(HUES)],
            'tilt': [0, 1.5, -1.5, 2.5, -2.5][len(machines) % 5],
            'shape': FORMES.get(cat, 'industrial'),
            'ar': ['16/10', '16/10', '4/3', '16/9', '5/4'][len(machines) % 5],
            'img': photo,
        }
        if photo:
            m['credit'] = {
                'img': photo,
                'auteur': (row.get('photo_credit') or '').strip(),
                'licence': (row.get('photo_licence') or 'Owned by ExportRev').strip(),
                'source': (row.get('photo_source') or '').strip(),
            }
        machines.append(m)

    if not machines:
        print('Nothing to publish — every row was rejected.')
        for i in ignores:
            print('  ' + i)
        return 1

    cats = sorted({m['cat'] for m in machines if m['cat']})
    mfrs = sorted({m['mfr'] for m in machines})
    photos = {m['ref']: m.pop('credit') for m in machines if 'credit' in m}

    io.open(os.path.join(ICI, 'assets', 'data.js'), 'w', encoding='utf-8').write(
        '/* GENERATED by import_stock.py from %s — do not edit by hand. */\n'
        'window.JX = %s;\nwindow.JX_CATS = %s;\nwindow.JX_MFRS = %s;\n'
        % (os.path.basename(chemin), json.dumps(machines, indent=0, sort_keys=True),
           json.dumps(cats), json.dumps(mfrs)))
    # Never silently wipe existing photo credits. An import with no photo
    # column would otherwise blank out every credit already on the site —
    # which, for CC BY images, turns a correct page into a licence breach.
    pj = os.path.join(ICI, 'assets', 'photos.js')
    if photos:
        if os.path.exists(pj):
            io.open(pj + '.bak', 'w', encoding='utf-8').write(
                io.open(pj, encoding='utf-8').read())
        io.open(pj, 'w', encoding='utf-8').write(
            '/* GENERATED by import_stock.py — do not edit by hand. */\n'
            'window.JX_PHOTOS = %s;\n' % json.dumps(photos, indent=0, sort_keys=True))
    elif os.path.exists(pj):
        alertes.append('your file listed no photos, so assets/photos.js was left '
                       'untouched — the credits already on the site are intact')

    print('published %d machines, %d categories, %d makes, %d photographs'
          % (len(machines), len(cats), len(mfrs), len(photos)))
    if alertes:
        print('\nworth a look (%d):' % len(alertes))
        for a in alertes[:20]:
            print('  ' + a)
    if ignores:
        print('\nskipped (%d):' % len(ignores))
        for i in ignores[:20]:
            print('  ' + i)
    print('\nNow run:  python3 src/checks.py http://127.0.0.1:8000/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
