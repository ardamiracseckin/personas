import subprocess


class AppleScriptError(Exception):
    pass


def run(script, timeout=30):
    """Run an AppleScript via osascript; return stdout. Raise AppleScriptError (Turkish) on failure."""
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AppleScriptError("İşlem zaman aşımına uğradı (uygulama yanıt vermedi).")
    if proc.returncode != 0:
        err = (proc.stderr or "").lower()
        if "not authorized" in err or "authoriz" in err or "-1743" in err:
            raise AppleScriptError(
                "İzin gerekli: System Settings > Privacy & Security > Automation'dan "
                "Terminal'e Mail/Takvim erişimi verin."
            )
        raise AppleScriptError(f"AppleScript hatası: {proc.stderr.strip()}")
    return proc.stdout.strip()
