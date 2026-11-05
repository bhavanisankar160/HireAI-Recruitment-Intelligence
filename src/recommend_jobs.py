
import pandas as pd
import json
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize(text):
    return str(text).strip().lower()


def parse_skills(value):
    if pd.isna(value):
        return []

    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [normalize(s) for s in parsed]
    except (json.JSONDecodeError, TypeError):
        pass

    return [
        normalize(s)
        for s in str(value).split(",")
        if s.strip()
    ]


# 1. Load datasets
candidates = pd.read_csv("data/candidate_profiles.csv")
jobs = pd.read_csv("data/jobs.csv")

# 2. Select candidate
candidate_index = 0
candidate = candidates.iloc[candidate_index]
candidate_skills = set(parse_skills(candidate["skills"]))

if not candidate_skills:
    raise SystemExit(
        "No skills found for this candidate. "
        "Check candidate_profiles.csv or select another candidate."
    )

# 3. Prepare job descriptions
jobs["job_text"] = (
    jobs["title"].fillna("").astype(str) + " " +
    jobs["description"].fillna("").astype(str) + " " +
    jobs["required_skills"].fillna("").astype(str)
)

# 4. Calculate TF-IDF similarity
documents = [
    " ".join(sorted(candidate_skills))
] + jobs["job_text"].tolist()

vectorizer = TfidfVectorizer(stop_words="english")
vectors = vectorizer.fit_transform(documents)

similarities = cosine_similarity(
    vectors[0:1], vectors[1:]
)[0] * 100

jobs["similarity_score"] = similarities

# 5. Calculate skill coverage and missing skills
coverage_scores = []
missing_skills_list = []

for _, job in jobs.iterrows():
    required = [
        normalize(skill)
        for skill in str(job["required_skills"]).split(",")
        if skill.strip()
    ]

    # Exact normalized skill matching
    matched = candidate_skills.intersection(required)
    missing = sorted(set(required) - candidate_skills)

    coverage = (
        len(matched) / len(set(required)) * 100
        if required else 0.0
    )

    coverage_scores.append(coverage)
    missing_skills_list.append(", ".join(missing) or "None")

jobs["skill_coverage"] = coverage_scores
jobs["missing_skills"] = missing_skills_list

# 6. Combined ranking score
jobs["combined_score"] = (
    0.4 * jobs["similarity_score"] +
    0.6 * jobs["skill_coverage"]
)

ranked = jobs.sort_values(
    "combined_score", ascending=False
)

# 7. Display results
print("\nAI RECRUITMENT INTELLIGENCE")
print("=" * 45)
print("Candidate ID:", candidate["ID"])
print("Resume category:", candidate["Category"])
print("Candidate skills:", ", ".join(sorted(candidate_skills)))

for _, job in ranked.head(5).iterrows():
    print(f"\nJob: {job['title']}")
    print(f"Text similarity: {job['similarity_score']:.2f}%")
    print(f"Skill coverage: {job['skill_coverage']:.2f}%")
    print(f"Combined score: {job['combined_score']:.2f}%")
    print(f"Missing skills: {job['missing_skills']}")

print("\nRecommendations completed!")
