import json
import subprocess
from pathlib import Path
from datetime import datetime

report_dir = Path("reports")
report_dir.mkdir(exist_ok=True)

with open(report_dir / "schema_changes.json") as f:
    changes = json.load(f)


def get_git_info():
    """Get latest commit id and author."""
    try:
        commit_id = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()

        user = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%an"],
            text=True
        ).strip()

    except Exception:
        commit_id = "Unknown"
        user = "Unknown"

    return user, commit_id


user, commit_id = get_git_info()

report = []

report.append("=" * 80)
report.append("SCHEMA DRIFT REPORT")
report.append("=" * 80)
report.append(f"Generated : {datetime.now():%Y-%m-%d %H:%M:%S}")
report.append(f"User      : {user}")
report.append(f"Commit ID : {commit_id}")
report.append("")


def section(title, values):
    report.append(title)

    if not values:
        report.append("  None")
    else:
        for v in values:
            report.append(f"  + {v}")

    report.append("")


section("Added Tables", changes["tables_added"])
section("Removed Tables", changes["tables_removed"])

section("Added Columns", changes["columns_added"])
section("Removed Columns", changes["columns_removed"])

report.append("Modified Columns")

if changes["columns_modified"]:
    for c in changes["columns_modified"]:
        report.append("")
        report.append(c["column"])
        report.append("OLD")
        report.append(json.dumps(c["old"], indent=4))
        report.append("NEW")
        report.append(json.dumps(c["new"], indent=4))
else:
    report.append("  None")

report.append("")

section("Added Indexes", changes["indexes_added"])
section("Removed Indexes", changes["indexes_removed"])

section("Added Views", changes["views_added"])
section("Removed Views", changes["views_removed"])

section("Added Functions", changes["functions_added"])
section("Removed Functions", changes["functions_removed"])

section("Added Triggers", changes["triggers_added"])
section("Removed Triggers", changes["triggers_removed"])

# Append instead of overwrite
with open(report_dir / "ddl_report.txt", "a", encoding="utf-8") as f:
    f.write("\n".join(report))
    f.write("\n\n")

print("DDL report appended successfully.")
