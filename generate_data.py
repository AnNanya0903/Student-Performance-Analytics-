"""
Generates a realistic sample dataset of 500+ student records for the
Student Performance Analytics Dashboard.

Run this once to create data/students.csv:
    python generate_data.py
"""
import numpy as np
import pandas as pd

np.random.seed(42)

N = 550

DEPARTMENTS = ["Computer Science", "Information Science", "Electronics", "Mechanical", "Civil"]
DEPT_WEIGHTS = [0.28, 0.22, 0.2, 0.16, 0.14]
GENDERS = ["Male", "Female", "Other"]
GENDER_WEIGHTS = [0.55, 0.43, 0.02]
LOCATIONS = ["Urban", "Semi-Urban", "Rural"]
LOCATION_WEIGHTS = [0.5, 0.3, 0.2]
SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Rohan", "Ananya", "Diya", "Saanvi", "Aadhya", "Kiara", "Myra",
    "Anika", "Navya", "Riya", "Priya", "Kabir", "Dev", "Yash", "Aryan",
    "Neha", "Pooja", "Sneha", "Meera", "Kavya", "Tanvi", "Rahul", "Karan",
    "Nikhil", "Varun", "Siddharth", "Akash", "Divya", "Nisha", "Simran", "Isha",
    "Manav", "Ritvik", "Om", "Aryaman", "Advait", "Zoya", "Fatima", "Ayesha",
    "Sara", "Amara",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Reddy", "Rao", "Iyer", "Nair", "Menon",
    "Kulkarni", "Joshi", "Patel", "Shah", "Mehta", "Chatterjee", "Banerjee",
    "Mukherjee", "Das", "Bose", "Pillai", "Krishnan", "Naidu", "Chauhan",
    "Malhotra", "Kapoor", "Bhatt", "Desai", "Rathod", "Yadav", "Mishra", "Pandey",
]

def gen_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

rng = np.random.default_rng(42)

rows = []
for i in range(1, N + 1):
    student_id = f"STU{i:04d}"
    name = gen_name(rng)
    gender = rng.choice(GENDERS, p=GENDER_WEIGHTS)
    age = int(np.clip(rng.normal(20.5, 1.5), 18, 26))
    department = rng.choice(DEPARTMENTS, p=DEPT_WEIGHTS)
    semester = int(rng.choice(SEMESTERS))
    location = rng.choice(LOCATIONS, p=LOCATION_WEIGHTS)
    internet_access = rng.choice(["Yes", "No"], p=[0.86, 0.14])
    extracurricular = rng.choice(["Yes", "No"], p=[0.4, 0.6])

    # Underlying "ability" factor drives correlated performance
    ability = np.clip(rng.normal(65, 15), 5, 100)
    study_hours = float(np.clip(rng.normal(4 + ability / 40, 3), 0, 35))
    attendance = float(np.clip(rng.normal(70 + ability / 6, 12), 30, 100))

    def score(base_shift=0, noise=10):
        val = ability + base_shift + rng.normal(0, noise) + (study_hours - 8) * 0.6
        return float(np.clip(val, 0, 100))

    math_score = score(rng.normal(0, 5))
    science_score = score(rng.normal(0, 5))
    programming_score = score(rng.normal(2, 6))
    english_score = score(rng.normal(-2, 6))
    assignment_score = score(5, 8)
    internal_score = score(0, 8)
    final_exam_score = score(-3, 9)

    rows.append(
        {
            "student_id": student_id,
            "name": name,
            "gender": gender,
            "age": age,
            "department": department,
            "semester": semester,
            "attendance_percentage": round(attendance, 1),
            "math_score": round(math_score, 1),
            "science_score": round(science_score, 1),
            "programming_score": round(programming_score, 1),
            "english_score": round(english_score, 1),
            "assignment_score": round(assignment_score, 1),
            "internal_score": round(internal_score, 1),
            "final_exam_score": round(final_exam_score, 1),
            "study_hours_per_week": round(study_hours, 1),
            "extracurricular": extracurricular,
            "internet_access": internet_access,
            "location": location,
        }
    )

df = pd.DataFrame(rows)

# Inject a small amount of realistic messiness so the cleaning pipeline
# has genuine work to do (duplicates, missing values, whitespace, bad types).
dup_rows = df.sample(8, random_state=1).copy()
df = pd.concat([df, dup_rows], ignore_index=True)

missing_idx = rng.choice(df.index, size=25, replace=False)
missing_cols = ["attendance_percentage", "math_score", "study_hours_per_week", "internal_score"]
for idx in missing_idx:
    col = rng.choice(missing_cols)
    df.loc[idx, col] = np.nan

# Whitespace / inconsistent casing in a few text fields
ws_idx = rng.choice(df.index, size=15, replace=False)
for idx in ws_idx:
    df.loc[idx, "department"] = f"  {df.loc[idx, 'department'].upper()}  "

# A few invalid / out-of-range numeric values
bad_idx = rng.choice(df.index, size=6, replace=False)
for idx in bad_idx:
    df.loc[idx, "final_exam_score"] = rng.choice([-5, 115, 250])

df = df.sample(frac=1, random_state=7).reset_index(drop=True)

df.to_csv("data/students.csv", index=False)
print(f"Generated {len(df)} rows -> data/students.csv")
