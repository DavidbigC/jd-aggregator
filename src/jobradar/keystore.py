import os
import re
import subprocess

SERVICE, ACCOUNT = "jobradar.deepseek", "api-key"
KEY_RE = re.compile(r"^sk-[A-Za-z0-9]{16,}$")


def get_key() -> tuple[str | None, str]:
    """The DeepSeek key and where it came from: the environment wins over the macOS Keychain."""
    if key := os.environ.get("DEEPSEEK_API_KEY"):
        return key, "env"
    r = subprocess.run(["security", "find-generic-password", "-s", SERVICE, "-a", ACCOUNT, "-w"],
                       capture_output=True, text=True)
    return (r.stdout.strip() or None), "keychain"


def set_key(key: str) -> None:
    if not KEY_RE.match(key):
        raise ValueError("not a DeepSeek key")
    # via stdin so the key never appears in the process list
    subprocess.run(["security", "-i"], input=f"add-generic-password -U -s {SERVICE} -a {ACCOUNT} -w {key}\n",
                   text=True, capture_output=True, check=True)


def delete_key() -> None:
    subprocess.run(["security", "delete-generic-password", "-s", SERVICE, "-a", ACCOUNT], capture_output=True)
