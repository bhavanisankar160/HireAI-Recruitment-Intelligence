
import pandas as pd

df = pd.read_csv("data/candidate_profiles.csv")

technical_skills = [
    "python", "sql", "java", "machine learning",
    "pandas", "aws", "docker", "react"
]

print("Searching for resumes with technical skills...\n")

found = 0

for index, row in df.iterrows():
    resume = str(row["Resume_str"]).lower()

    matches = [
        skill for skill in technical_skills
        if skill in resume
    ]

    if len(matches) >= 3:
        print("Candidate index:", index)
        print("Candidate ID:", row["ID"])
        print("Category:", row["Category"])
        print("Skills found in resume:", matches)
        print("-" * 40)

        found += 1

    if found >= 10:
        break

if found == 0:
    print("No resumes found with at least 3 listed skills.")
