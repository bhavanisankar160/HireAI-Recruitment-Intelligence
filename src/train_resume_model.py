
import pandas as pd
import re
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# 1. Load cleaned resumes
df = pd.read_csv("data/cleaned_resumes.csv")

df = df.dropna(subset=["Resume_str", "Category"])
df = df[df["Resume_str"].str.strip() != ""]

X = df["Resume_str"].astype(str)
y = df["Category"].astype(str)

print("Total resumes:", len(df))
print("Number of categories:", y.nunique())

# 2. Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training resumes:", len(X_train))
print("Testing resumes:", len(X_test))

# 3. Create the ML pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            stop_words="english",
            max_features=20000,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        )
    )
])

# 4. Train the model
print("\nTraining model...")
model.fit(X_train, y_train)

# 5. Evaluate on unseen test data
predictions = model.predict(X_test)

print("\nAccuracy:",
      round(accuracy_score(y_test, predictions), 4))

print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))

# 6. Save the trained model
Path("models").mkdir(exist_ok=True)

joblib.dump(model, "models/resume_classifier.joblib")

print("\nModel saved to models/resume_classifier.joblib")

# 7. Test on a sample resume
sample_resume = """
Python developer with SQL, pandas, machine learning,
data analysis and scikit-learn project experience.
"""

predicted_category = model.predict([sample_resume])[0]

print("\nSample resume prediction:", predicted_category)
