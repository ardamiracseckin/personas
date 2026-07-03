from app.tools import applescript

_READ_TODAY = '''
set output to ""
set startDate to current date
set hours of startDate to 0
set minutes of startDate to 0
set seconds of startDate to 0
set endDate to startDate + (1 * days)
tell application "Calendar"
  repeat with cal in calendars
    repeat with ev in (every event of cal whose start date >= startDate and start date < endDate)
      set output to output & (summary of ev) & "|" & (start date of ev as string) & linefeed
    end repeat
  end repeat
end tell
return output
'''

_CREATE = '''
set startDate to (current date)
set year of startDate to {y}
set month of startDate to {mo}
set day of startDate to {d}
set hours of startDate to {h}
set minutes of startDate to {mi}
set seconds of startDate to 0
set endDate to startDate + ({dur} * minutes)
tell application "Calendar"
  tell calendar 1
    make new event with properties {{summary:"{title}", start date:startDate, end date:endDate}}
  end tell
end tell
return "ok"
'''


def parse_events(raw):
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        title, start = line.split("|", 1)
        events.append({"title": title.strip(), "start": start.strip()})
    return events


def get_events(when="today", run_fn=None):
    run_fn = run_fn or applescript.run
    raw = run_fn(_READ_TODAY)
    return parse_events(raw)


def create_event(title, year, month, day, hour, minute, duration_min=60, run_fn=None):
    """Create a calendar event. Only ever called after explicit user confirmation."""
    run_fn = run_fn or applescript.run
    script = _CREATE.format(
        title=title.replace('"', "'"),
        y=year, mo=month, d=day, h=hour, mi=minute, dur=duration_min,
    )
    run_fn(script)
    return True
