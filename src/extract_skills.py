
import re
import json

# Skill dictionary
SKILLS = [
     "python", "java", "c++", "c#", "sql",
    "machine learning", "deep learning",
    "data analysis", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch",
    "nlp", "aws", "docker", "kubernetes",
    "react", "javascript", "html", "css",
    "fastapi", "flask", "postgresql", "git",
    "excel", "power bi", "tableau"
]

# Extract skills from text
def extract_skills(resume_text):
    text = resume_text.lower()
    found = []

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):
            found.append(skill)

    return found


# Sample resume
resume = """
Computer Science student with Python, SQL,
machine learning, Pandas, scikit-learn and AWS.
Built a web application using React and FastAPI.
Used Docker to deploy a project.
"""

# Extract skills
skills = extract_skills(resume)

# Create structured candidate profile
candidate = {
    "candidate_name": "Sample Candidate",
    "skills": skills,
    "total_skills": len(skills)
}

print("EXTRACTED SKILLS")
print("----------------")
for skill in skills:
    print("-", skill)

print("\nCANDIDATE PROFILE")
print(json.dumps(candidate, indent=4))
