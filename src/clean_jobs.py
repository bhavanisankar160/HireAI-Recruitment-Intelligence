
import pandas as pd
import re

# Load the resume dataset
df = pd.read_csv("data/Resume.csv")

print("Original shape:", df.shape)

# Keep only useful columns
df = df[["ID", "Resume_str", "Category"]].copy()

# Remove missing values
df = df.dropna(subset=["Resume_str", "Category"])

# Clean resume text
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

df["Resume_str"] = df["Resume_str"].apply(clean_text)
df["Category"] = df["Category"].str.strip()

# Remove empty resumes and duplicate records
df = df[df["Resume_str"] != ""]
df = df.drop_duplicates(subset=["Resume_str"])

# Save cleaned dataset
df.to_csv("data/cleaned_resumes.csv", index=False)

print("Cleaned shape:", df.shape)
print("Missing values:\n", df.isnull().sum())
print("\nTop 10 categories:")
print(df["Category"].value_counts().head(10))

print("\nCleaned dataset saved successfully!")
