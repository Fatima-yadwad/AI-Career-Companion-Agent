import pandas as pd

p = r"data\raw\linkdin_Job_data.csv\linkdin_Job_data.csv"

df = pd.read_csv(p)

text = (
    df["job"].fillna("").astype(str)
    + " "
    + df["job_details"].fillna("").astype(str)
).str.lower()

mask = text.str.contains(r"\bintern(ship)?\b", regex=True)

cols = [
    "job_ID",
    "job",
    "company_name",
    "location",
    "work_type",
    "job_details"
]

x = df.loc[mask, cols].drop_duplicates("job_ID")

print("INTERNSHIP RECORDS:", len(x))
print("\n--- SAMPLE INTERNSHIPS ---")

for i, (_, row) in enumerate(x.head(30).iterrows(), 1):
    details = str(row["job_details"]).replace("\n", " ")[:500]

    print(f"\n[{i}] {row['job']} | {row['company_name']} | {row['location']}")
    print(details)
