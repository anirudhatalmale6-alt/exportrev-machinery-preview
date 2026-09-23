# -*- coding: utf-8 -*-
"""Machinery marketplace preview — automatic checks.

Run against the PUBLISHED page, not a local copy:

    python3 src/checks.py
    python3 src/checks.py http://127.0.0.1:8000/

Exit code is non-zero if anything fails, so it drops straight into CI.
The suite prints its own total; that total is the figure quoted for this
project, and anyone can recount it by running this file.
"""

import sys
import urllib.request

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1
        else 'https://anirudhatalmale6-alt.github.io/exportrev-machinery-preview/')
if not BASE.endswith('/'):
    BASE += '/'

ok = [0]
ko = [0]


def t(nom, cond, detail=''):
    if cond:
        ok[0] += 1
        print('  ok    %s' % nom)
    else:
        ko[0] += 1
        print('  ECHEC %s   %s' % (nom, detail))


def head(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            return r.status
    except Exception as e:
        return getattr(e, 'code', 0)


def main():
    print('machinery marketplace preview')
    print('  %s' % BASE)
    errs = []
    failed = []

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 900})
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append('uncaught: %s' % str(e)[:120]))
        pg.on('response', lambda r: failed.append('%s %s' % (r.status, r.url))
              if r.status >= 400 else None)

        resp = pg.goto(BASE, wait_until='domcontentloaded')
        pg.wait_for_timeout(1500)

        # ---- the page ----
        t('the page answers 200', resp is not None and resp.status == 200)
        t('the title names ExportRev', 'exportrev' in pg.title().lower(), pg.title())
        t('the title says what is sold', 'machinery' in pg.title().lower() or
          'equipment' in pg.title().lower(), pg.title())
        t('the html declares a language',
          bool(pg.evaluate("document.documentElement.getAttribute('lang')")))
        t('there is a viewport meta', pg.evaluate("!!document.querySelector('meta[name=viewport]')"))
        desc = pg.evaluate("(document.querySelector('meta[name=description]')||{}).content||''")
        t('the description meta is filled in', len(desc.strip()) > 30)
        t('exactly one h1', pg.evaluate("document.querySelectorAll('h1').length") == 1)
        t('there is a main landmark', pg.evaluate("!!document.querySelector('main')"))
        t('the stylesheet is published', head(BASE + 'assets/style.css') == 200)
        t('the script is published', head(BASE + 'assets/app.js') == 200)
        t('the inventory data is published', head(BASE + 'assets/data.js') == 200)

        # ---- nothing here may look like someone else's stock ----
        # Normalise whitespace: the banner is wrapped across lines in the HTML,
        # so a raw textContent match on "is reproduced" fails on the newline.
        avis = ' '.join((pg.evaluate(
            "(document.querySelector('.avis')||{}).textContent||''") or '').split())
        t('the demonstration banner is present', 'Demonstration' in avis)
        t('the banner says no real listing is reproduced',
          'no listing' in avis.lower() and 'is reproduced' in avis.lower())
        t('the banner names Machineryline as NOT copied',
          'machineryline' in avis.lower())
        pied = ' '.join((pg.evaluate("document.querySelector('footer').textContent") or '').split())
        t('the footer repeats that it is not a commercial offer',
          'not a commercial offer' in pied.lower())
        t('the footer disclaims any affiliation', 'not affiliated' in pied.lower())
        t('the footer says where the styling came from',
          'exportrev.com' in pied.lower())
        # The client asked for it "sur le meme ton" as exportrev.com. Assert the
        # palette really is ExportRev's green, so a later edit cannot drift it.
        t('the header carries ExportRev green, not the aircraft red', pg.evaluate(
            "(()=>{const c=getComputedStyle(document.querySelector('header')).backgroundColor;"
            "const m=c.match(/\\d+/g).map(Number);return m[1]>120 && m[1]>m[0]+60 && m[1]>m[2]+60;})()"))
        t('the page sits on a light body, like exportrev.com', pg.evaluate(
            "(()=>{const m=getComputedStyle(document.body).backgroundColor.match(/\\d+/g).map(Number);"
            "return m[0]>225 && m[1]>225 && m[2]>225;})()"))
        t('the hero keeps the diagonal cut', pg.evaluate(
            "getComputedStyle(document.querySelector('.hero'),'::after').clipPath.includes('polygon')"))
        t('the typeface follows exportrev.com', pg.evaluate(
            "getComputedStyle(document.body).fontFamily.toLowerCase().includes('roboto')"))
        t('the counter of copied listings reads zero', pg.evaluate(
            "Array.from(document.querySelectorAll('.ch')).some(c=>"
            "/Real listings copied/i.test(c.textContent) && /(^|\\D)0(\\D|$)/.test(c.textContent))"))
        t('no listing carries a dealer name or phone field', pg.evaluate(
            "window.JX.every(l=>!('company' in l) && !('phone' in l) && !('description' in l))"))

        # ---- inventory ----
        n = pg.evaluate("document.querySelectorAll('.card').length")
        t('the grid renders every machine', n >= 80, 'count=%s' % n)
        t('the data and the grid agree', n == pg.evaluate("window.JX.length"))
        t('every card has a plate, drawn or photographed', pg.evaluate(
            "Array.from(document.querySelectorAll('.card .plate'))"
            ".every(p=>p.querySelector('svg')||p.querySelector('img'))"))
        t('every card is a real button, not a clickable div', pg.evaluate(
            "Array.from(document.querySelectorAll('.card')).every(c=>c.tagName==='BUTTON')"))
        t('no image is loaded from outside this site', pg.evaluate(
            "Array.from(document.images).every(i=>i.src.startsWith(location.origin))"))

        # ---- the models must belong to their make ----
        # This is the machinery equivalent of drawing a helicopter as an airliner.
        t('no Liebherr model is badged as a Doosan', pg.evaluate(
            "!window.JX.some(l=>l.mfr==='DOOSAN' && /^R /.test(l.model))"))
        t('no Hitachi model is badged as a Liebherr', pg.evaluate(
            "!window.JX.some(l=>l.mfr==='LIEBHERR' && /^ZX/.test(l.model))"))
        t('no Grove model is badged as a Terex', pg.evaluate(
            "!window.JX.some(l=>l.mfr==='TEREX' && /^(GMK|GRT)/.test(l.model))"))
        t('no make and model pair is repeated', pg.evaluate(
            "(()=>{const s=new Set(window.JX.map(l=>l.mfr+'|'+l.model));"
            "return s.size===window.JX.length;})()"))

        # ---- silhouettes ----
        familles = pg.evaluate("Array.from(new Set(window.JX.map(l=>l.shape)))")
        t('several machine families are drawn, not one generic box',
          len(familles) >= 8, str(len(familles)))
        t('excavators are drawn as excavators', pg.evaluate(
            "window.JX.filter(l=>l.cat==='Excavators').every(l=>l.shape==='excavator')"))
        t('cranes are drawn as cranes', pg.evaluate(
            "window.JX.filter(l=>l.cat==='Cranes').every(l=>l.shape==='crane')"))
        t('spare parts are not drawn as a machine', pg.evaluate(
            "window.JX.filter(l=>l.cat==='Spare parts').every(l=>l.shape==='parts')"))

        # ---- specifications that belong to this trade ----
        t('machines carry an operating weight', pg.evaluate(
            "window.JX.filter(l=>l.cat!=='Spare parts').every(l=>l.weight>0)"))
        t('machines carry a power figure', pg.evaluate(
            "window.JX.filter(l=>l.cat!=='Spare parts' && l.cat!=='Industrial equipment')"
            ".every(l=>l.power>0)"))
        t('spare parts have no operating hours', pg.evaluate(
            "window.JX.filter(l=>l.cat==='Spare parts').every(l=>!l.hours)"))
        t('every machine has a yard and a country', pg.evaluate(
            "window.JX.every(l=>l.city.length>1 && l.country.length>1)"))

        # ---- category section is built from the data ----
        cartes = pg.evaluate("document.querySelectorAll('#cats [data-cat]').length")
        t('the category section lists every category',
          cartes == pg.evaluate("window.JX_CATS.length"), '%s cards' % cartes)
        t('the category counts add up to the inventory', pg.evaluate(
            "(()=>{const n=Array.from(document.querySelectorAll('#cats .et'))"
            ".reduce((a,e)=>a+parseInt(e.textContent,10),0);return n===window.JX.length;})()"))

        # ---- filters really filter ----
        total = n
        pg.select_option('#fcat', 'Cranes')
        pg.wait_for_timeout(400)
        grues = pg.evaluate("document.querySelectorAll('.card').length")
        t('the category filter reduces the grid', 0 < grues < total, '%s of %s' % (grues, total))
        t('every card left is in that category', pg.evaluate(
            "Array.from(document.querySelectorAll('.mason .ctype')).every(e=>e.textContent==='Cranes')"))
        t('the counter follows the filter',
          str(grues) in pg.evaluate("document.querySelector('#compte').textContent"))
        pg.select_option('#fcat', '')
        pg.wait_for_timeout(350)
        t('clearing the filter restores every card',
          pg.evaluate("document.querySelectorAll('.card').length") == total)

        pg.click('#cats [data-cat="Excavators"]')
        pg.wait_for_timeout(700)
        t('clicking a category card drives the filter',
          pg.evaluate("document.querySelector('#fcat').value") == 'Excavators')
        t('and the grid follows it', pg.evaluate(
            "Array.from(document.querySelectorAll('.mason .ctype')).every(e=>e.textContent==='Excavators')"))
        pg.select_option('#fcat', '')
        pg.wait_for_timeout(350)

        pg.fill('#fq', 'zzzznotamachine')
        pg.wait_for_timeout(400)
        t('a search with no match empties the grid',
          pg.evaluate("document.querySelectorAll('.card').length") == 0)
        t('and says so instead of showing nothing at all',
          pg.evaluate("!document.querySelector('#vide').hidden"))
        pg.fill('#fq', '')
        pg.wait_for_timeout(350)

        pg.evaluate("(()=>{const r=document.querySelector('#fprix');"
                    "r.value=r.min;r.dispatchEvent(new Event('input'));})()")
        pg.wait_for_timeout(400)
        t('the price ceiling removes the expensive machines',
          pg.evaluate("document.querySelectorAll('.card').length") < total)
        pg.evaluate("(()=>{const r=document.querySelector('#fprix');"
                    "r.value=r.max;r.dispatchEvent(new Event('input'));})()")
        pg.wait_for_timeout(400)
        t('raising the ceiling brings them back',
          pg.evaluate("document.querySelectorAll('.card').length") == total)

        pg.select_option('#ftri', 'price-asc')
        pg.wait_for_timeout(400)
        prix = pg.evaluate("Array.from(document.querySelectorAll('.mason .prix'))"
                           ".map(e=>Number(e.textContent.replace(/[^0-9]/g,'')))")
        t('sorting by price ascending really sorts', prix == sorted(prix))
        pg.select_option('#ftri', 'price-desc')
        pg.wait_for_timeout(350)

        # ---- detail sheet ----
        pg.click('.card')
        pg.wait_for_timeout(600)
        t('clicking a card opens the detail sheet', pg.evaluate("document.querySelector('#detail').open"))
        t('the sheet names the machine',
          len((pg.evaluate("document.querySelector('#dtitre').textContent") or '').strip()) > 6)
        t('the sheet shows a price',
          '€' in (pg.evaluate("document.querySelector('#dprix').textContent") or ''))
        t('the sheet shows the operating weight',
          (pg.evaluate("document.querySelector('#dpoids').textContent") or '').strip() not in ('', '—'))
        t('the sheet shows the power',
          (pg.evaluate("document.querySelector('#dpuiss').textContent") or '').strip() not in ('', '—'))
        t('the sheet states where the picture came from',
          len((pg.evaluate("document.querySelector('#dcredit').textContent") or '').strip()) > 20)
        pg.click('#dfermer')
        pg.wait_for_timeout(400)
        t('the sheet closes again', not pg.evaluate("document.querySelector('#detail').open"))

        # ---- photographs, if any, on licence terms we can defend ----
        photos = pg.evaluate("window.JX.filter(l=>l.img).length")
        if photos:
            t('every photograph is served from this site, never hotlinked', pg.evaluate(
                "window.JX.filter(l=>l.img).every(l=>!/^https?:/i.test(l.img))"))
            t('every photograph names its author', pg.evaluate(
                "window.JX.filter(l=>l.img).every(l=>l.credit && l.credit.auteur.length>1)"))
            t('every photograph names its licence', pg.evaluate(
                "window.JX.filter(l=>l.img).every(l=>l.credit && l.credit.licence.length>1)"))
            t('every licence used permits reuse', pg.evaluate(
                "window.JX.filter(l=>l.img).every(l=>/public domain|cc0|cc by/i.test(l.credit.licence))"))
            t('every photograph links back to its source page', pg.evaluate(
                "window.JX.filter(l=>l.img).every(l=>"
                "/^https:\\/\\/commons\\.wikimedia\\.org\\//.test(l.credit.source))"))
            t('the credit is printed on every photographed card',
              pg.evaluate("document.querySelectorAll('.card .credit').length") == photos)
            t('no image that has loaded is broken', pg.evaluate(
                "Array.from(document.images).filter(i=>i.complete).every(i=>i.naturalWidth>0)"))

        # ---- feedback ----
        t('the review cards are marked as templates',
          pg.evaluate("document.querySelectorAll('.gabtag').length") >= 3)
        t('no review is presented as a real person', pg.evaluate(
            "Array.from(document.querySelectorAll('#feedback .fb')).every(c=>c.classList.contains('gab'))"))
        t('the rating control has five stars',
          pg.evaluate("document.querySelectorAll('.stars button').length") == 5)
        pg.evaluate("document.querySelectorAll('.stars button')[3].click()")
        pg.wait_for_timeout(250)
        t('choosing a rating lights the stars up to it',
          pg.evaluate("document.querySelectorAll('.stars button[aria-pressed=true]').length") == 4)
        pg.fill('#fbnom', 'Check Suite')
        pg.evaluate("document.querySelector('#fbform').requestSubmit()")
        pg.wait_for_timeout(450)
        t('submitting gives the visitor an answer',
          len((pg.evaluate("document.querySelector('#fbok').textContent") or '').strip()) > 10)
        t('and says nothing left the browser',
          'nothing was sent' in (pg.evaluate("document.querySelector('#fbok').textContent") or '').lower())

        # ---- accessibility and layout ----
        t('every button has an accessible name', pg.evaluate(
            "Array.from(document.querySelectorAll('button')).every(b=>"
            "((b.textContent||'').trim()||b.getAttribute('aria-label')||'').length>0)"))
        t('every form field has a label', pg.evaluate(
            "Array.from(document.querySelectorAll('input,select,textarea'))"
            ".filter(e=>e.type!=='range'&&e.type!=='submit')"
            ".every(e=>!!document.querySelector('label[for=\"'+e.id+'\"]'))"))
        t('no positive tabindex anywhere', pg.evaluate(
            "!document.querySelector('[tabindex]:not([tabindex=\"0\"]):not([tabindex=\"-1\"])')"))

        for w in (390, 768, 1280):
            pg.set_viewport_size({'width': w, 'height': 900})
            pg.wait_for_timeout(350)
            sw = pg.evaluate('document.documentElement.scrollWidth')
            t('no horizontal overflow at %spx' % w, sw <= w + 1, 'scrollWidth=%s' % sw)

        pg.set_viewport_size({'width': 390, 'height': 780})
        pg.wait_for_timeout(400)
        t('the grid collapses to one column on a phone',
          pg.evaluate("getComputedStyle(document.querySelector('.mason')).columnCount") in ('1', 'auto'))

        t('the console reported no error', not errs, '; '.join(errs[:3]))
        t('no request failed', not failed, '; '.join(failed[:3]))

        pg.close()
        b.close()

    total_checks = ok[0] + ko[0]
    print('')
    print('  %s checks, %s passed, %s failed' % (total_checks, ok[0], ko[0]))
    sys.exit(1 if ko[0] else 0)


if __name__ == '__main__':
    main()
