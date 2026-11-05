
import pandas as pd
import json

df = pd.read_csv("data/candidate_profiles.csv")

for index in [0, 925, 928]:
    row = df.iloc[index]

    print("\n" + "=" * 45)
    print("Index:", index)
    print("ID:", row["ID"])
    print("Category:", row["Category"])

    raw_skills = row.get("skills", "[]")
    print("Raw skills:", repr(raw_skills))

    try:
        skills = json.loads(raw_skills) if isinstance(raw_skills, str) else []
    except json.JSONDecodeError:
        skills = []

    print("Parsed skills:", skills)
