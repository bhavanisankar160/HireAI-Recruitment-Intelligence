from pathlib import Path
from io import BytesIO
import json
import ast
import re

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent.parent


# ---------- FastAPI application ----------

app = FastAPI(
    title="AI Recruitment Intelligence API",
    description="Resume classification and job recommendations",
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Load datasets ----------

jobs_path = ROOT / "data" / "jobs.csv"
candidates_path = ROOT / "data" / "candidate_profiles.csv"

if not jobs_path.exists():
    raise RuntimeError("Missing jobs.csv in the data folder.")

jobs = pd.read_csv(jobs_path)

if candidates_path.exists():
    candidates = pd.read_csv(candidates_path)
else:
    candidates = pd.DataFrame()


# ---------- Request schemas ----------

class RecommendationRequest(BaseModel):
    candidate_index: int = Field(default=0, ge=0)
    top_k: int = Field(default=5, ge=1, le=20)


class CandidateIdRecommendationRequest(BaseModel):
    candidate_id: str
    top_k: int = Field(default=5, ge=1, le=20)


# ---------- Skill processing ----------

def normalize_skill(skill):
    skill = str(skill).strip().lower()
    return re.sub(r"\s+", " ", skill)


def parse_skills(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        items = list(value)

    else:
        try:
            if pd.isna(value):
                return []
        except (TypeError, ValueError):
            pass

        text = str(value).strip()

        if not text:
            return []

        items = None

        # Try JSON list
        try:
            parsed = json.loads(text)

            if isinstance(parsed, list):
                items = parsed

        except (json.JSONDecodeError, TypeError):
            pass

        # Try Python-style list
        if items is None and text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)

                if isinstance(parsed, list):
                    items = parsed

            except (ValueError, SyntaxError):
                pass

        # Fall back to comma-separated values
        if items is None:
            items = text.split(",")

    return sorted({
        normalize_skill(skill)
        for skill in items
        if skill is not None and normalize_skill(skill)
    })


# ---------- Validate datasets ----------
if jobs.empty:
    raise RuntimeError("jobs.csv contains no jobs.")

if not candidates.empty:
    candidate_columns = {"ID", "Category", "skills"}

    if not candidate_columns.issubset(candidates.columns):
        raise RuntimeError(
            f"Candidate dataset must contain: {sorted(candidate_columns)}"
        )

job_columns = {"job_id", "title", "required_skills"}

if not job_columns.issubset(jobs.columns):
    raise RuntimeError(
        f"Job dataset must contain: {sorted(job_columns)}"
    )

if "description" not in jobs.columns:
    jobs["description"] = ""


# ---------- Prepare job data ----------

jobs["required_list"] = jobs["required_skills"].apply(parse_skills)

jobs["job_text"] = (
    jobs["title"].fillna("").astype(str)
    + " "
    + jobs["description"].fillna("").astype(str)
    + " "
    + jobs["required_list"].apply(lambda skills: " ".join(skills))
)

vectorizer = TfidfVectorizer(stop_words="english")
job_vectors = vectorizer.fit_transform(jobs["job_text"].tolist())


# ---------- Related skills ----------

# These are predefined relationships, not learned by an AI model.
RELATED_SKILLS = {
    "data analysis": {"pandas", "statistics"},
    "pandas": {"data analysis"},
    "python programming": {"python"},
    "python": {"python programming"},
    "machine learning": {"scikit-learn", "sklearn"},
    "scikit-learn": {"sklearn", "machine learning"},
    "sklearn": {"scikit-learn", "machine learning"},
    "database management": {"sql"},
    "sql": {"database management"},
    "postgresql": {"sql"},
    "mysql": {"sql"},
    "javascript": {"react"},
    "react": {"javascript"},
    "aws": {"cloud computing"},
    "cloud computing": {"aws"},
}


def match_skills(candidate_skills, required_skills):
    """
    Match exact skills and explicitly configured related skills.

    Returns:
        matched_skills: job requirements satisfied by the candidate
        missing_skills: job requirements not matched
    """
    candidate_skill_set = {
        normalize_skill(skill) for skill in candidate_skills
    }

    required_set = {
        normalize_skill(skill) for skill in required_skills
    }

    matched = set()

    for required in required_set:

        # Exact match
        if required in candidate_skill_set:
            matched.add(required)
            continue

        # Related skill match
        for candidate_skill in candidate_skill_set:
            related = RELATED_SKILLS.get(candidate_skill, set())

            if required in related:
                matched.add(required)
                break

    missing = required_set - matched

    return sorted(matched), sorted(missing)


# ---------- Recommendation engine ----------

def generate_recommendations(candidate_skills, candidate_text, top_k=5):
    # Normalize and remove duplicate candidate skills
    candidate_skill_set = {
        normalize_skill(skill)
        for skill in candidate_skills
        if normalize_skill(skill)
    }

    # Calculate text similarity
    candidate_vector = vectorizer.transform([str(candidate_text)])
    similarities = cosine_similarity(candidate_vector, job_vectors)[0] * 100

    results = []

    for position, (_, job) in enumerate(jobs.iterrows()):
        # Remove duplicate required skills
        required = sorted(set(job["required_list"]))

        # Match exact and configured related skills
        matched, missing = match_skills(candidate_skill_set, required)

        # Calculate skill coverage
        coverage = (
            len(matched) / len(required) * 100
            if required else 0.0
        )

        similarity = float(similarities[position])

        # Combined score: 70% skill coverage + 30% text similarity
        combined = (0.70 * coverage) + (0.30 * similarity)

        results.append({
            "job_id": str(job["job_id"]),
            "title": str(job["title"]),
            "combined_score": round(combined, 2),
            "similarity_score": round(similarity, 2),
            "skill_coverage": round(coverage, 2),
            "matched_skill_count": len(matched),
            "required_skill_count": len(required),
            "matched_skills": matched,
            "missing_skills": missing,
            "match_explanation": (
                f"{len(matched)} of {len(required)} required skills matched."
            )
        })

    # Rank jobs from highest to lowest match score
    results.sort(
        key=lambda item: item["combined_score"],
        reverse=True
    )

    return results[:top_k]


# ---------- Home ----------

@app.get("/")
def home():
    return {
        "message": "AI Recruitment Intelligence API is running",
        "docs": "/docs",
    }


# ---------- Health check ----------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "candidate_count": len(candidates),
        "job_count": len(jobs),
    }


# ---------- Dashboard statistics ----------

@app.get("/stats")
def dashboard_stats():
    candidate_skills = set()

    for skills in candidates["skills"]:
        candidate_skills.update(parse_skills(skills))

    job_skills = set()

    for skills in jobs["required_list"]:
        job_skills.update(skills)

    return {
        "total_candidates": len(candidates),
        "total_jobs": len(jobs),
        "total_unique_skills": len(candidate_skills | job_skills),
        "matching_engine": "TF-IDF + Semantic Skill Matching",
    }


# ---------- Debug candidate ----------

@app.get("/debug/candidate/{index}")
def debug_candidate(index: int):

    if index < 0 or index >= len(candidates):
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    candidate = candidates.iloc[index]

    return {
        "candidate_id": str(candidate["ID"]),
        "raw_skills": str(candidate["skills"]),
        "parsed_skills": parse_skills(candidate["skills"]),
    }


# ---------- Debug jobs ----------

@app.get("/debug/jobs")
def debug_jobs():
    return [
        {
            "job_id": str(job["job_id"]),
            "title": str(job["title"]),
            "required_skills": job["required_list"],
        }
        for _, job in jobs.iterrows()
    ]


# ---------- Recommendations by candidate index ----------

@app.post("/recommend")
def recommend(request: RecommendationRequest):

    if request.candidate_index >= len(candidates):
        raise HTTPException(
            status_code=404,
            detail="Candidate index not found",
        )

    candidate = candidates.iloc[request.candidate_index]

    candidate_skills = parse_skills(candidate["skills"])

    if not candidate_skills:
        raise HTTPException(
            status_code=422,
            detail="No extracted skills found for this candidate",
        )

    recommendations = generate_recommendations(
        candidate_skills=candidate_skills,
        candidate_text=" ".join(candidate_skills),
        top_k=request.top_k,
    )

    return {
        "candidate_id": str(candidate["ID"]),
        "resume_category": str(candidate["Category"]),
        "candidate_skills": candidate_skills,
        "recommendations": recommendations,
    }


# ---------- Recommendations by candidate ID ----------

@app.post("/recommend-by-id")
def recommend_by_id(request: CandidateIdRecommendationRequest):

    requested_id = request.candidate_id.strip()

    matches = candidates[
        candidates["ID"].astype(str).str.strip() == requested_id
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Candidate ID not found",
        )

    candidate = matches.iloc[0]
    candidate_skills = parse_skills(candidate["skills"])

    if not candidate_skills:
        raise HTTPException(
            status_code=422,
            detail="No extracted skills found for this candidate",
        )

    recommendations = generate_recommendations(
        candidate_skills=candidate_skills,
        candidate_text=" ".join(candidate_skills),
        top_k=request.top_k,
    )

    return {
        "candidate_id": str(candidate["ID"]),
        "resume_category": str(candidate["Category"]),
        "candidate_skills": candidate_skills,
        "recommendations": recommendations,
    }


# ---------- Get candidate by ID ----------

@app.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str):

    matches = candidates[
        candidates["ID"].astype(str).str.strip()
        == candidate_id.strip()
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    row = matches.iloc[0]

    return {
        "candidate_id": str(row["ID"]),
        "resume_category": str(row["Category"]),
        "candidate_skills": parse_skills(row["skills"]),
    }


# ---------- PDF resume upload ----------

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume.",
        )

    contents = await file.read()

    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file.",
        )

    try:
        reader = PdfReader(BytesIO(contents))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Password-protected PDFs are not supported.",
            )

        extracted_pages = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_pages.append(page_text)

        resume_text = "\n".join(extracted_pages).strip()

        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text found. "
                    "This may be a scanned PDF."
                ),
            )

        # Identify known skills from the job dataset.
        all_skills = {
            skill
            for skills in jobs["required_list"]
            for skill in skills
        }

        resume_lower = normalize_skill(resume_text)

        extracted_skills = sorted([
            skill
            for skill in all_skills
            if re.search(
                r"(?<!\w)" + re.escape(skill) + r"(?!\w)",
                resume_lower,
            )
        ])

        if not extracted_skills:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No recognized job-related skills found "
                    "in the resume."
                ),
            )

        recommendations = generate_recommendations(
            candidate_skills=extracted_skills,
            candidate_text=resume_text,
            top_k=5,
        )

        return {
            "filename": file.filename,
            "resume_text_preview": resume_text[:300],
            "extracted_skills": extracted_skills,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(exc)}",
        )

    finally:
        await file.close()
