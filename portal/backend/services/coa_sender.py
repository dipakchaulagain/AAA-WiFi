from __future__ import annotations

import subprocess


def disconnect_session(nas_ip: str, nas_secret: str, session_id: str, username: str) -> bool:
    attrs = f"Acct-Session-Id={session_id},User-Name={username}\n"
    try:
        proc = subprocess.run(
            ["radclient", "-x", f"{nas_ip}:3799", "disconnect", nas_secret],
            input=attrs.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
        )
        out = (proc.stdout or b"").decode("utf-8", errors="replace")
        return "Disconnect-ACK" in out
    except subprocess.TimeoutExpired:
        return False

