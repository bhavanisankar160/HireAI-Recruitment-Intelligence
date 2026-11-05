
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Starter job dataset
jobs = pd.DataFrame([
    {
        "title": "Machine Learning Engineer",
        "skills": "Python machine learning scikit-learn pandas "
                  "deep learning model deployment"
    },
    {
        "title": "Data Analyst",
        "skills": "Python SQL Excel Power BI statistics "
                  "data visualization pandas"
    },
    {
        "title": "Backend Developer",
        "skills": "Python Java REST API FastAPI SQL "
                  "PostgreSQL Docker"
    },
    {
        "title": "NLP Engineer",
        "skills": "Python NLP text processing transformers "
                  "machine learning embeddings"
    },
    {
        "title": "Cloud Engineer",
        "skills": "AWS Docker Kubernetes Linux networking "
                  "CI CD cloud deployment"
    },
    {
        "title": "Data Scientist",
        "skills": "Python statistics machine learning "
                  "pandas SQL data visualization"
    }
])

# 2. Example candidate resume
resume = """
Third-year Computer Science student.
Skills: Python, Pandas, SQL, machine learning,
scikit-learn, data analysis and data visualization.
Projects: Sales prediction and customer analytics.
"""

# 3. Combine resume and job text
documents = [resume] + jobs["skills"].tolist()

# 4. Convert text into numerical TF-IDF vectors
vectorizer = TfidfVectorizer(stop_words="english")
vectors = vectorizer.fit_transform(documents)

# 5. Compare the resume with every job
scores = cosine_similarity(vectors[0:1], vectors[1:])[0]

# 6. Rank jobs by similarity score
jobs["match_score"] = scores * 100
ranked_jobs = jobs.sort_values(
    by="match_score", ascending=False
)

# 7. Display the results
print("\nAI JOB RECOMMENDATIONS")
print("-" * 45)

for _, job in ranked_jobs.iterrows():
    print(f"\nJob: {job['title']}")
    print(f"Text similarity: {job['match_score']:.2f}%")
    print(f"Skills: {job['skills']}")
