"""Apple Rehber'den kişi arama.

Alıcıyı isimle söyleyebilmek için ("Ahmet'e mail at") gerekli. Veri cihazdan
çıkmaz; yalnızca taslakta kullanıcıya gösterilir.
"""
from app.tools import applescript

_FIND = '''
set output to ""
tell application "Contacts"
  repeat with p in (people whose name contains "{name}")
    set e to ""
    repeat with em in emails of p
      set e to e & (value of em) & ";"
    end repeat
    set ph to ""
    repeat with pn in phones of p
      set ph to ph & (value of pn) & ";"
    end repeat
    set output to output & (name of p) & "|" & e & "|" & ph & linefeed
  end repeat
end tell
return output
'''


def parse_people(raw):
    kisiler = []
    for satir in (raw or "").splitlines():
        satir = satir.strip()
        if not satir or satir.count("|") < 2:
            continue
        ad, epostalar, telefonlar = satir.split("|", 2)
        kisiler.append({
            "name": ad.strip(),
            "emails": [e.strip() for e in epostalar.split(";") if e.strip()],
            "phones": [t.strip() for t in telefonlar.split(";") if t.strip()],
        })
    return kisiler


def find_people(name, run_fn=None):
    """Adı verilen metni içeren kişiler. AppleScript izni yoksa boş liste döner."""
    run_fn = run_fn or applescript.run
    guvenli = (name or "").replace('"', "'").strip()
    if not guvenli:
        return []
    try:
        return parse_people(run_fn(_FIND.replace("{name}", guvenli)))
    except Exception:
        return []


def with_email(kisiler):
    return [k for k in kisiler if k["emails"]]


def with_phone(kisiler):
    return [k for k in kisiler if k["phones"]]
