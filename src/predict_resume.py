
import joblib

# Load the saved model
model = joblib.load("models/resume_classifier.joblib")

# Enter a sample resume
resume = """
Computer Science student with Python, SQL,
Pandas, machine learning and data analysis skills.
Developed projects using Scikit-learn.
"""

# Predict the category
prediction = model.predict([resume])[0]

print("Predicted Resume Category:", prediction)

# Show the top 3 predicted categories, if supported
if hasattr(model, "predict_proba"):
    probabilities = model.predict_proba([resume])[0]
    categories = model.classes_

    top_indices = probabilities.argsort()[-3:][::-1]

    print("\nTop 3 predicted categories:")
    for i in top_indices:
        print(f"{categories[i]}: {probabilities[i]:.2%}")
