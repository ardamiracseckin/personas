from app.tools import applescript

_READ_UNREAD = '''
set output to ""
tell application "Mail"
  set msgs to (messages of inbox whose read status is false)
  set n to 0
  repeat with m in msgs
    if n >= {limit} then exit repeat
    set output to output & (subject of m) & "|" & (sender of m) & linefeed
    set n to n + 1
  end repeat
end tell
return output
'''

_SEND = '''
tell application "Mail"
  set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{body}", visible:true}}
  tell newMessage
    make new to recipient at end of to recipients with properties {{address:"{to}"}}
  end tell
  send newMessage
end tell
return "ok"
'''


def parse_mails(raw):
    mails = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        subject, sender = line.split("|", 1)
        mails.append({"subject": subject.strip(), "sender": sender.strip()})
    return mails


def get_recent(unread_only=True, limit=10, run_fn=None):
    run_fn = run_fn or applescript.run
    raw = run_fn(_READ_UNREAD.replace("{limit}", str(limit)))
    return parse_mails(raw)


def send_mail(to, subject, body, run_fn=None):
    """Send an email via Apple Mail. Only ever called after explicit user confirmation."""
    run_fn = run_fn or applescript.run
    script = _SEND.format(
        to=to,
        subject=subject.replace('"', "'"),
        body=body.replace('"', "'").replace("\n", " "),
    )
    run_fn(script)
    return True
