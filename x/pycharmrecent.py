import datetime as dt
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

config_root = Path.home() / "Library/Application Support/JetBrains"

files = [
    p
    for p in config_root.glob("PyCharm*/options/recentProjects.xml")
    if p.is_file()
]

if not files:
    raise SystemExit(f"No recentProjects.xml found beneath {config_root}")

source = max(files, key=lambda p: p.stat().st_mtime)

stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path.home() / "Desktop" / f"pycharm-recentProjects-{stamp}.xml"
shutil.copy2(source, backup)

print(f"Reading: {source}")
print(f"Backup:  {backup}")
print()

root = ET.parse(backup).getroot()
entries = root.findall(
    ".//component[@name='RecentProjectsManager']"
    "/option[@name='additionalInfo']/map/entry"
)

def millis(options, name):
    value = options.get(name)
    try:
        return int(value) if value else 0
    except ValueError:
        return 0

def format_time(value):
    if not value:
        return "unknown"
    return (
        dt.datetime
        .fromtimestamp(value / 1000)
        .astimezone()
        .strftime("%Y-%m-%d %H:%M:%S %Z")
    )

rows = []

for entry in entries:
    meta = entry.find("./value/RecentProjectMetaInfo")
    if meta is None:
        continue

    options = {
        option.get("name"): option.get("value")
        for option in meta.findall("./option")
    }

    path = entry.get("key", "").replace("$USER_HOME$", str(Path.home()))

    rows.append({
        "path": path,
        "opened": meta.get("opened") == "true",
        "opened_at": millis(options, "projectOpenTimestamp"),
        "activated_at": millis(options, "activationTimestamp"),
    })

open_rows = sorted(
    (row for row in rows if row["opened"]),
    key=lambda row: (row["activated_at"], row["opened_at"]),
    reverse=True,
)

print("PROJECTS MARKED OPEN IN THE LAST SAVED STATE")
print("================================================")
if not open_rows:
    print("(none — PyCharm may already have overwritten the opened flags)")
else:
    for row in open_rows:
        print(row["path"])
        print(f"    last focused: {format_time(row['activated_at'])}")
        print(f"    last opened:  {format_time(row['opened_at'])}")

print()
print("ALL PROJECTS, SORTED BY ACTUAL LAST-OPEN TIME")
print("================================================")
for row in sorted(rows, key=lambda row: row["opened_at"], reverse=True):
    marker = "  [OPEN]" if row["opened"] else ""
    print(f"{format_time(row['opened_at'])}  {row['path']}{marker}")

