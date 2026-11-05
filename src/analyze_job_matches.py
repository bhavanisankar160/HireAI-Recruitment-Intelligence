
import pandas as pd
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------- Skill parsing ----------
def parse_skills(value):
    if pd.isna(value):
        return []

    try:
        result = json.loads(value)
        if isinstance(result, list):
            return [
                str(skill).strip().lower()
                for skill in result
                if str(skill).strip()
            ]
    except (json.JSONDecodeError, TypeError):
        pass

    return [
        skill.strip().lower()
        for skill in str(value).split(",")
        if skill.strip()
    ]


# ---------- Load datasets ----------
ROOT = Path(__file__).resolve().parent.parent

candidates = pd.read_csv(ROOT / "data" / "candidate_profiles.csv")
jobs = pd.read_csv(ROOT / "data" / "jobs.csv")

if candidates.empty or jobs.empty:
    raise ValueError("Candidate or job dataset is empty.")

required_columns = {"ID", "Category", "skills"}
if not required_columns.issubset(candidates.columns):
    raise ValueError("Candidate dataset is missing required columns.")

required_job_columns = {
    "job_id", "title", "description", "required_skills"
}
if not required_job_columns.issubset(jobs.columns):
    raise ValueError("Job dataset is missing required columns.")


# ---------- Select candidate ----------
print("\nAvailable candidate indices: 0 to", len(candidates) - 1)
candidate_index = int(input("Enter candidate index (e.g. 928): "))

if not 0 <= candidate_index < len(candidates):
    raise ValueError("Candidate index is outside the valid range.")

candidate = candidates.iloc[candidate_index]
candidate_skills = set(parse_skills(candidate["skills"]))

if not candidate_skills:
    raise ValueError(
        "This candidate has no extracted skills. Try another index."
    )


# ---------- Normalize job requirements ----------
jobs["required_list"] = jobs["required_skills"].apply(parse_skills)

# ---------- Build TF-IDF job representations ----------
candidate_text = " ".join(sorted(candidate_skills))

jobs["job_text"] = (
    jobs["title"].fillna("").astype(str) + " " +
    jobs["description"].fillna("").astype(str) + " " +
    jobs["required_skills"].fillna("").astype(str)
)

documents = [candidate_text] + jobs["job_text"].tolist()

vectorizer = TfidfVectorizer(stop_words="english")
vectors = vectorizer.fit_transform(documents)

similarities = cosine_similarity(
    vectors[0:1], vectors[1:]
)[0] * 100


# ---------- Calculate explainable scores ----------
results = []

for position, (_, job) in enumerate(jobs.iterrows()):
    required = set(job["required_list"])
    matched = sorted(candidate_skills & required)
    missing = sorted(required - candidate_skills)

    coverage = (
        len(matched) / len(required) * 100
        if required else 0.0
    )

    similarity = float(similarities[position])

    # Prototype ranking formula
    combined = 0.4 * similarity + 0.6 * coverage

    results.append({
        "job_id": job["job_id"],
        "title": job["title"],
        "similarity": similarity,
        "coverage": coverage,
        "combined_score": combined,
        "matched_skills": matched,
        "missing_skills": missing
    })


# ---------- Rank and display ----------
results.sort(
    key=lambda item: item["combined_score"],
    reverse=True
)

print("\nEXPLAINABLE JOB RECOMMENDATIONS")
print("=" * 45)
print("Candidate ID:", candidate["ID"])
print("Resume category:", candidate["Category"])
print("Candidate skills:", ", ".join(sorted(candidate_skills)))

for rank, result in enumerate(results[:5], start=1):
    print(f"\n#{rank} {result['title']}")
    print(f"Combined score: {result['combined_score']:.2f}%")
    print(f"Text similarity: {result['similarity']:.2f}%")
    print(f"Skill coverage: {result['coverage']:.2f}%")
    print(
        "Matched skills:",
        ", ".join(result["matched_skills"]) or "None"
    )
    print(
        "Missing skills:",
        ", ".join(result["missing_skills"]) or "None"
    )

print("\nAnalysis completed!")
@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    # Validate PDF file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume."
        )

    try:
        contents = await file.read()

        if not contents.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid PDF."
            )

        # Extract text from PDF
        reader = PdfReader(BytesIO(contents))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Password-protected PDFs are not supported."
            )

        resume_text = " ".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in the PDF."
            )

        # Detect skills
        skill_list = sorted({
            skill
            for skills in jobs["required_list"]
            for skill in skills
        })

        resume_lower = resume_text.lower()
        extracted_skills = []

        for skill in skill_list:
            pattern = (
                r"(?<!\w)"
                + re.escape(skill.lower())
                + r"(?!\w)"
            )

            if re.search(pattern, resume_lower):
                extracted_skills.append(skill)

        # Calculate job recommendations
        resume_vector = job_vectorizer.transform([resume_text])
        similarities = cosine_similarity(
            resume_vector, job_vectors
        )[0]

        recommendations = []

        for i, job in jobs.iterrows():
            required = job["required_list"]

            matched = [
                skill for skill in required
                if skill in extracted_skills
            ]

            missing = [
                skill for skill in required
                if skill not in extracted_skills
            ]

            coverage = (
                len(matched) / len(required) * 100
                if required else 0
            )

            similarity = float(similarities[i] * 100)

            score = 0.7 * coverage + 0.3 * similarity

            recommendations.append({
                "job_id": str(job["job_id"]),
                "title": job["title"],
                "matched_skills": matched,
                "missing_skills": missing,
                "skill_coverage": round(coverage, 2),
                "text_similarity": round(similarity, 2),
                "match_score": round(score, 2)
            })

        recommendations.sort(
            key=lambda x: x["match_score"],
            reverse=True
        )

        return {
            "filename": file.filename,
            "extracted_skills": extracted_skills,
            "recommendations": recommendations[:5]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(e)}"
        )