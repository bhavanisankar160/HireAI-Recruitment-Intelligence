
import pandas as pd
import re
import json
from pathlib import Path
from time import perf_counter

# 1. Load cleaned resumes
input_file = Path("data/cleaned_resumes.csv")
output_file = Path("data/candidate_profiles.csv")

df = pd.read_csv(input_file)

print("Total resumes loaded:", len(df))

# 2. Define technical skills
SKILLS = [
    "python", "java", "c++", "c#", "sql",
    "machine learning", "deep learning",
    "data analysis", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch",
    "nlp", "aws", "docker", "kubernetes",
    "react", "javascript", "html", "css",
    "fastapi", "flask", "postgresql", "git",
    "excel", "power bi", "tableau",
    "spring boot", "linux", "rest api"
]

# 3. Compile regex patterns once
SKILL_PATTERNS = {
    skill: re.compile(
        r"(?<!\w)" + re.escape(skill) + r"(?!\w)",
        re.IGNORECASE
    )
    for skill in SKILLS
}

# 4. Extract skills from a resume
def extract_skills(text):
    text = str(text)
    found = []

    for skill, pattern in SKILL_PATTERNS.items():
        if pattern.search(text):
            found.append(skill)

    return found

# 5. Validate required columns
required_columns = ["ID", "Resume_str", "Category"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# 6. Clean input rows
df = df.dropna(
    subset=["Resume_str", "Category"]
).copy()

df["Resume_str"] = df["Resume_str"].astype(str)
df = df[df["Resume_str"].str.strip() != ""]

# 7. Extract skills from all resumes
print("\nStarting skill extraction...")
start = perf_counter()

df["skills"] = df["Resume_str"].apply(extract_skills)
df["skill_count"] = df["skills"].apply(len)

elapsed = perf_counter() - start
print(f"Extraction completed in {elapsed:.2f} seconds")

# 8. Store skill lists as JSON strings
df["skills"] = df["skills"].apply(
    lambda skills: json.dumps(skills)
)

# 9. Save candidate profiles
output_file.parent.mkdir(
    parents=True, exist_ok=True
)

df.to_csv(output_file, index=False)

# 10. Display results
print("\nBatch extraction completed!")
print("Total resumes processed:", len(df))
print(
    "Average skills per resume:",
    round(df["skill_count"].mean(), 2)
)

print("\nSample candidate profiles:")
print(
    df[["ID", "Category", "skills", "skill_count"]]
    .head(5)
    .to_string(index=False)
)

print(f"\nSaved: {output_file}")
