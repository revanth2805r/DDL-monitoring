import json
from pathlib import Path

previous = Path("schema_snapshots/previous.json")
latest = Path("schema_snapshots/latest.json")

if not previous.exists():
    print("First snapshot.")
    exit()

with open(previous) as f:
    old = json.load(f)

with open(latest) as f:
    new = json.load(f)

changes = {
    "tables_added": [],
    "tables_removed": [],
    "columns_added": [],
    "columns_removed": [],
    "columns_modified": [],
    "indexes_added": [],
    "indexes_removed": [],
    "views_added": [],
    "views_removed": [],
    "functions_added": [],
    "functions_removed": [],
    "triggers_added": [],
    "triggers_removed": []
}

#########################################
# TABLES
#########################################

old_tables = old["tables"]
new_tables = new["tables"]

for table in new_tables:
    if table not in old_tables:
        changes["tables_added"].append(table)

for table in old_tables:
    if table not in new_tables:
        changes["tables_removed"].append(table)

#########################################
# COLUMNS
#########################################

for table in new_tables:

    if table not in old_tables:
        continue

    old_cols = {c["name"]: c for c in old_tables[table]["columns"]}
    new_cols = {c["name"]: c for c in new_tables[table]["columns"]}

    for c in new_cols:
        if c not in old_cols:
            changes["columns_added"].append(f"{table}.{c}")

    for c in old_cols:
        if c not in new_cols:
            changes["columns_removed"].append(f"{table}.{c}")

    for c in new_cols:
        if c in old_cols:
            if new_cols[c] != old_cols[c]:
                changes["columns_modified"].append({
                    "column": f"{table}.{c}",
                    "old": old_cols[c],
                    "new": new_cols[c]
                })

#########################################
# Generic object compare
#########################################

def compare_objects(old_dict, new_dict, added, removed):

    for k in new_dict:
        if k not in old_dict:
            changes[added].append(k)

    for k in old_dict:
        if k not in new_dict:
            changes[removed].append(k)

compare_objects(old["indexes"],new["indexes"],
                "indexes_added","indexes_removed")

compare_objects(old["views"],new["views"],
                "views_added","views_removed")

compare_objects(old["functions"],new["functions"],
                "functions_added","functions_removed")

compare_objects(old["triggers"],new["triggers"],
                "triggers_added","triggers_removed")

with open("reports/schema_changes.json","w") as f:
    json.dump(changes,f,indent=4)

print("Comparison completed.")