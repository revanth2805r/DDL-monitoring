import os
import json
import psycopg2
from pathlib import Path
from datetime import datetime

# ---------------------------------------
# Output Directory
# ---------------------------------------

OUTPUT_DIR = Path("schema_snapshots")
OUTPUT_DIR.mkdir(exist_ok=True)

LATEST_FILE = OUTPUT_DIR / "latest.json"
PREVIOUS_FILE = OUTPUT_DIR / "previous.json"

# Move previous snapshot
if LATEST_FILE.exists():
    if PREVIOUS_FILE.exists():
        PREVIOUS_FILE.unlink()
    LATEST_FILE.rename(PREVIOUS_FILE)

# ---------------------------------------
# Read Database Configuration
# ---------------------------------------

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

required = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
}

missing = [key for key, value in required.items() if not value]

if missing:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing)}"
    )

print("Connecting to PostgreSQL...")
print(f"Host     : {DB_HOST}")
print(f"Port     : {DB_PORT}")
print(f"Database : {DB_NAME}")
print(f"User     : {DB_USER}")

# ---------------------------------------
# Connect to PostgreSQL
# ---------------------------------------

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)

cur = conn.cursor()

schema = {
    "generated_at": datetime.utcnow().isoformat(),
    "tables": {},
    "views": {},
    "indexes": {},
    "functions": {},
    "triggers": {}
}

#########################################
# TABLES + COLUMNS
#########################################

cur.execute("""
SELECT
table_schema,
table_name,
column_name,
ordinal_position,
data_type,
character_maximum_length,
numeric_precision,
numeric_scale,
is_nullable,
column_default
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY table_schema, table_name, ordinal_position;
""")

for row in cur.fetchall():
    (
        schema_name,
        table,
        column,
        position,
        dtype,
        charlen,
        precision,
        scale,
        nullable,
        default,
    ) = row

    key = f"{schema_name}.{table}"

    schema["tables"].setdefault(
        key,
        {
            "columns": [],
            "constraints": []
        }
    )

    schema["tables"][key]["columns"].append(
        {
            "name": column,
            "type": dtype,
            "length": charlen,
            "precision": precision,
            "scale": scale,
            "nullable": nullable,
            "default": default,
        }
    )

#########################################
# CONSTRAINTS
#########################################

cur.execute("""
SELECT
tc.table_schema,
tc.table_name,
tc.constraint_name,
tc.constraint_type,
kcu.column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
ON tc.constraint_name = kcu.constraint_name
AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema NOT IN
('pg_catalog','information_schema')
ORDER BY tc.table_schema, tc.table_name;
""")

for row in cur.fetchall():
    schema_name, table, cname, ctype, column = row

    key = f"{schema_name}.{table}"

    if key not in schema["tables"]:
        continue

    schema["tables"][key]["constraints"].append(
        {
            "name": cname,
            "type": ctype,
            "column": column,
        }
    )

#########################################
# INDEXES
#########################################

cur.execute("""
SELECT
schemaname,
tablename,
indexname,
indexdef
FROM pg_indexes
WHERE schemaname NOT IN
('pg_catalog','information_schema');
""")

for row in cur.fetchall():
    schema_name, table, name, definition = row

    schema["indexes"][name] = {
        "table": f"{schema_name}.{table}",
        "definition": definition,
    }

#########################################
# VIEWS
#########################################

cur.execute("""
SELECT
table_schema,
table_name,
view_definition
FROM information_schema.views
WHERE table_schema NOT IN
('pg_catalog','information_schema');
""")

for row in cur.fetchall():
    schema_name, name, definition = row

    schema["views"][f"{schema_name}.{name}"] = definition

#########################################
# FUNCTIONS
#########################################

cur.execute("""
SELECT
n.nspname,
p.proname,
pg_get_functiondef(p.oid)
FROM pg_proc p
JOIN pg_namespace n
ON n.oid = p.pronamespace
WHERE n.nspname NOT IN
('pg_catalog','information_schema');
""")

for row in cur.fetchall():
    schema_name, name, definition = row

    schema["functions"][f"{schema_name}.{name}"] = definition

#########################################
# TRIGGERS
#########################################

cur.execute("""
SELECT
event_object_schema,
event_object_table,
trigger_name,
action_timing,
event_manipulation
FROM information_schema.triggers;
""")

for row in cur.fetchall():
    schema_name, table, trigger, timing, event = row

    schema["triggers"][trigger] = {
        "table": f"{schema_name}.{table}",
        "timing": timing,
        "event": event,
    }

cur.close()
conn.close()

with open(LATEST_FILE, "w") as f:
    json.dump(schema, f, indent=4)

print(f"Schema snapshot created successfully: {LATEST_FILE}")
