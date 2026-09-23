# -*- coding: utf-8 -*-
"""Generate the DEMONSTRATION inventory for the machinery marketplace preview.

Same engine as the aircraft preview — the filtering, the masonry and the detail
sheet do not care what is being sold. What changes is the vocabulary and the
specifications: an excavator is judged on operating hours, weight and bucket
capacity, not on airframe time.

The category tree follows the ordinary trade vocabulary of the sector (the same
words every dealer uses: excavators, loaders, cranes, dumpers…). Nothing is
copied from any existing marketplace: no listing, no photograph, no seller.

Deterministic: a fixed seed, so a rebuild does not reshuffle the grid.

    python3 gen_data.py   ->  assets/data.js
"""

import io
import json
import os
import random

ICI = os.path.dirname(os.path.abspath(__file__))
RND = random.Random(20260920)

# (category, silhouette family, {make: [models that make actually builds]},
#  price band, weight band t, power band hp, how many to generate)
#
# Models are bound to their manufacturer on purpose. Pairing a random make with
# a random model inside a category produces things like "DOOSAN R 926" — a
# Liebherr model under a Doosan badge. An equipment buyer spots that in a
# second, exactly like a helicopter drawn as an airliner.
FAMILLES = [
    ('Trucks and heavy vehicles', 'truck', {
        'MERCEDES-BENZ': ['Actros 1845', 'Actros 2551', 'Arocs 3242', 'Arocs 4145'],
        'SCANIA': ['R 450', 'R 500', 'G 410', 'S 500'],
        'VOLVO': ['FH 460', 'FH 500', 'FMX 500', 'FM 420'],
        'MAN': ['TGX 18.510', 'TGS 35.440', 'TGS 33.470'],
        'DAF': ['XF 480', 'CF 450', 'XG 530'],
        'IVECO': ['S-Way 480', 'Trakker 410'],
        'RENAULT TRUCKS': ['T High 520', 'K 440', 'C 480'],
     }, (14_000, 128_000), (7, 33), (320, 620), 12),

    ('Excavators', 'excavator', {
        'CATERPILLAR': ['320 GC', '323 F', '336 F', '349 F'],
        'KOMATSU': ['PC210LC-11', 'PC290LC-11', 'PC360LC-11'],
        'HITACHI': ['ZX210LC-6', 'ZX300LC-6', 'ZX350LC-6'],
        'VOLVO': ['EC220E', 'EC300E', 'EC250E'],
        'LIEBHERR': ['R 920', 'R 926', 'R 938'],
        'DOOSAN': ['DX225LC-5', 'DX300LC-5'],
        'JCB': ['JS220', 'JS300', 'JZ140'],
        'HYUNDAI': ['HX220L', 'HX300L'],
     }, (28_000, 310_000), (14, 36), (110, 300), 14),

    ('Loaders', 'loader', {
        'CATERPILLAR': ['950 GC', '966 M', '980 M'],
        'VOLVO': ['L110H', 'L150H', 'L120H'],
        'KOMATSU': ['WA320-8', 'WA470-8', 'WA380-8'],
        'LIEBHERR': ['L 538', 'L 556', 'L 566'],
        'JCB': ['427 ZX', '437 HT'],
        'CASE': ['821G', '921G'],
        'BOBCAT': ['S770', 'S650'],
     }, (24_000, 280_000), (8, 31), (130, 360), 9),

    ('Cranes', 'crane', {
        'LIEBHERR': ['LTM 1050-3.1', 'LTM 1090-4.2', 'LTM 1130-5.1'],
        'GROVE': ['GMK 4100L', 'GMK 5250L', 'GRT 8100'],
        'TEREX': ['AC 100-4L', 'AC 45 City'],
        'TADANO': ['ATF 220G-5', 'ATF 130G-5'],
        'SANY': ['STC800', 'SAC 1000S'],
        'MANITOWOC': ['MLC 100-1', 'GHC 55'],
     }, (90_000, 980_000), (36, 96), (340, 720), 8),

    ('Bulldozers', 'dozer', {
        'CATERPILLAR': ['D6 XE', 'D8T', 'D9T'],
        'KOMATSU': ['D51PX-24', 'D65PX-18', 'D85EX-18'],
        'LIEBHERR': ['PR 736', 'PR 746'],
        'JOHN DEERE': ['850L', '750L'],
        'SHANTUI': ['SD16', 'SD22'],
     }, (46_000, 520_000), (15, 49), (150, 450), 7),

    ('Dumpers and haulers', 'dumper', {
        'CATERPILLAR': ['725 C2', '730 EJ', '740 GC'],
        'VOLVO': ['A30G', 'A40G', 'A25G'],
        'BELL': ['B30E', 'B45E'],
        'KOMATSU': ['HM300-5', 'HM400-5'],
        'HYDREMA': ['912HM', '922D'],
     }, (52_000, 430_000), (18, 45), (300, 520), 6),

    ('Concrete equipment', 'mixer', {
        'PUTZMEISTER': ['M 36-4', 'M 42-5', 'M 52-5'],
        'SCHWING': ['S 36 X', 'S 43 SX'],
        'CIFA': ['K45H', 'Carbotech 47-5'],
        'LIEBHERR': ['HTM 905', 'HTM 1204'],
        'SANY': ['SYM5423', 'SYG5230'],
     }, (38_000, 390_000), (12, 38), (280, 480), 6),

    ('Material handling', 'forklift', {
        'MANITOU': ['MT 1840', 'MRT 2550', 'MT 625'],
        'JCB': ['540-170', '535-95'],
        'LINDE': ['H50D', 'H80D'],
        'TOYOTA': ['8FGU25', '8FBMT30'],
        'HYSTER': ['H3.0FT', 'H5.5FT'],
        'MERLO': ['P 40.17', 'P 27.6'],
        'KALMAR': ['DCG 90-45'],
     }, (16_000, 210_000), (3, 22), (75, 280), 8),

    ('Road construction equipment', 'roller', {
        'BOMAG': ['BW 213 D-5', 'BW 174 AP'],
        'HAMM': ['H 13i', 'HD+ 120i'],
        'DYNAPAC': ['CA 2500D', 'CC 2200'],
        'CATERPILLAR': ['CS11 GC', 'CB 13'],
        'WIRTGEN': ['W 100 F', 'W 210 Fi'],
        'VOGELE': ['Super 1800-3', 'Super 1300-3'],
     }, (22_000, 290_000), (7, 26), (100, 320), 6),

    ('Drilling machinery', 'drill', {
        'SANDVIK': ['DP1500i', 'DI650i'],
        'EPIROC': ['SmartROC T35', 'FlexiROC T30'],
        'SOILMEC': ['SR-45', 'SR-65'],
        'BAUER': ['BG 28', 'BG 36'],
        'CASAGRANDE': ['B 250', 'C 600'],
     }, (85_000, 760_000), (18, 62), (250, 560), 4),

    ('Mining equipment', 'mining', {
        'CATERPILLAR': ['793F', '777G'],
        'KOMATSU': ['PC1250-11', 'HD785-8'],
        'SANDVIK': ['LH517i', 'TH551i'],
        'EPIROC': ['MT6020', 'Scooptram ST18'],
        'LIEBHERR': ['R 9200', 'R 9150'],
     }, (180_000, 1_900_000), (45, 180), (500, 1600), 4),

    ('Industrial equipment', 'industrial', {
        'ATLAS COPCO': ['XAS 88', 'XATS 350'],
        'CATERPILLAR': ['C9 genset', 'C15 genset'],
        'HIMOINSA': ['HFW 200', 'HRFW 100'],
        'KAESER': ['M 125', 'M 250'],
        'WACKER NEUSON': ['G 70', 'G 25'],
     }, (6_000, 120_000), (1, 12), (40, 220), 5),

    ('Spare parts', 'parts', {
        'CATERPILLAR': ['Final drive assembly', 'Undercarriage set', 'Bucket 1.2 m3'],
        'KOMATSU': ['Hydraulic pump', 'Swing motor'],
        'VOLVO': ['Turbocharger', 'Gearbox'],
        'LIEBHERR': ['Final drive assembly', 'Boom cylinder'],
        'ZF': ['Gearbox', 'Axle assembly'],
        'BOSCH REXROTH': ['Hydraulic pump', 'Control valve'],
     }, (900, 42_000), (0, 3), (0, 0), 6),
]

# Deliberately generic yards. No dealer from any real marketplace appears here.
DEPOTS = [
    ('Rotterdam', 'Netherlands'), ('Antwerp', 'Belgium'), ('Hamburg', 'Germany'),
    ('Lyon', 'France'), ('Milan', 'Italy'), ('Valencia', 'Spain'),
    ('Gdansk', 'Poland'), ('Gothenburg', 'Sweden'), ('Dubai', 'United Arab Emirates'),
    ('Casablanca', 'Morocco'), ('Montreal', 'Canada'), ('Istanbul', 'Turkiye'),
]

ETATS = ['Available', 'Available', 'Available', 'Under offer', 'Just listed']


def arrondi(n):
    if n >= 500_000:
        return int(round(n / 10_000.0) * 10_000)
    if n >= 100_000:
        return int(round(n / 2_500.0) * 2_500)
    if n >= 10_000:
        return int(round(n / 500.0) * 500)
    return int(round(n / 100.0) * 100)


def main():
    listings = []
    ref = 7200
    for (cat, forme, catalogue, (lo, hi), (wlo, whi),
         (plo, phi), combien) in FAMILLES:
        # every real (make, model) pair this category can offer, sampled without
        # repetition so the grid never shows the same machine twice
        paires = [(mk, md) for mk, mds in sorted(catalogue.items()) for md in mds]
        RND.shuffle(paires)
        for marque, modele in paires[:combien]:
            ref += 3
            an = RND.randint(2004, 2024)
            age = (2025 - an) / 21.0
            prix = arrondi(hi - (hi - lo) * (age ** 0.8) * RND.uniform(.7, 1.0))
            listings.append({
                'ref': 'JM-%d' % ref,
                'cat': cat,
                'mfr': marque,
                'model': modele,
                'year': an,
                'price': max(prix, lo),
                # machinery is judged on operating hours, not airframe time
                'hours': 0 if cat == 'Spare parts' else int(RND.uniform(900, 18500)),
                'weight': 0 if whi == 0 else round(RND.uniform(wlo, whi), 1),
                'power': 0 if phi == 0 else int(RND.uniform(plo, phi)),
                'city': RND.choice(DEPOTS)[0],
                'country': '',
                'status': RND.choice(ETATS),
                # green family, to sit inside ExportRev's palette
                'hue': RND.choice([96, 104, 112, 120, 128, 136, 144, 88]),
                'tilt': round(RND.uniform(-3.5, 3.5), 1),
                'shape': forme,
                'ar': RND.choice(['16/10', '16/10', '4/3', '16/9', '5/4']),
                'img': '',
            })
    # fix the country to match the city actually drawn
    villes = dict(DEPOTS)
    for l in listings:
        l['country'] = villes[l['city']]

    RND.shuffle(listings)
    cats = sorted({l['cat'] for l in listings})
    mfrs = sorted({l['mfr'] for l in listings})
    out = ('/* GENERATED by gen_data.py — do not edit by hand.\n'
           '   Demonstration inventory. Makes and models are real product names;\n'
           '   years, hours, weights, prices, references and yards are generated. */\n'
           'window.JX = %s;\nwindow.JX_CATS = %s;\nwindow.JX_MFRS = %s;\n' % (
               json.dumps(listings, indent=0, sort_keys=True),
               json.dumps(cats), json.dumps(mfrs)))
    io.open(os.path.join(ICI, 'assets', 'data.js'), 'w', encoding='utf-8').write(out)
    print('%d demo machines, %d categories, %d makes' % (
        len(listings), len(cats), len(mfrs)))
    print('price range %s - %s' % (min(l['price'] for l in listings),
                                   max(l['price'] for l in listings)))


if __name__ == '__main__':
    main()
