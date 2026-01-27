import csv

def load_bugs_from_csv(path: str):
    bugs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bugs.append({
                "id": row.get("id"),
                "title": row.get("title"),
                "component": row.get("component"),
                "severity": row.get("severity"),
                "created_date": row.get("created_date"),
                "closed_date": row.get("closed_date") or None,
                "text": row.get("text"),
            })
    return bugs
