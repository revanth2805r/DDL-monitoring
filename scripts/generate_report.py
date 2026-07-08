import json
from pathlib import Path
from datetime import datetime

report_dir = Path("reports")
report_dir.mkdir(exist_ok=True)

with open("reports/schema_changes.json") as f:
    changes = json.load(f)

report = []

report.append("SCHEMA DRIFT REPORT")
report.append("=" * 60)
report.append(f"Generated : {datetime.now()}")
report.append("")

def section(title, values):

    report.append(title)

    if not values:
        report.append("  None")
    else:
        for v in values:
            report.append(f"  + {v}")

    report.append("")

section("Added Tables",changes["tables_added"])
section("Removed Tables",changes["tables_removed"])

section("Added Columns",changes["columns_added"])
section("Removed Columns",changes["columns_removed"])

report.append("Modified Columns")

if changes["columns_modified"]:

    for c in changes["columns_modified"]:

        report.append("")
        report.append(c["column"])
        report.append("OLD")
        report.append(json.dumps(c["old"],indent=4))
        report.append("NEW")
        report.append(json.dumps(c["new"],indent=4))

else:
    report.append("  None")

report.append("")

section("Added Indexes",changes["indexes_added"])
section("Removed Indexes",changes["indexes_removed"])

section("Added Views",changes["views_added"])
section("Removed Views",changes["views_removed"])

section("Added Functions",changes["functions_added"])
section("Removed Functions",changes["functions_removed"])

section("Added Triggers",changes["triggers_added"])
section("Removed Triggers",changes["triggers_removed"])

with open("reports/ddl_report.txt","w") as f:
    f.write("\n".join(report))

print("DDL report generated.")