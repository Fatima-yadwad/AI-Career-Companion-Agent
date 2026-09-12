# M2 — RAG & Job-Resume Matching Evaluation

## 1. Objective

The objective of M2 evaluation is to validate the internship knowledge base, semantic retrieval pipeline, and Job-Resume Matching Agent using sample student profiles.

The evaluation verifies whether the system can:

- Retrieve relevant internship and early-career opportunities from the curated job knowledge base.
- Match a student's skills and profile against retrieved job requirements.
- Generate a compatibility score.
- Identify matched and missing skills.
- Provide an explanation for why a job is suitable for the candidate.
- Rank suitable jobs based on compatibility.

---

## 2. Evaluation Setup

### Job Knowledge Base

| Metric              |                                Result |
| ------------------- | ------------------------------------: |
| Curated job records |                                   102 |
| Semantic chunks     |                                   388 |
| Embedding dimension |                                   384 |
| Vector index        |                                 FAISS |
| Embedding model     |                      all-MiniLM-L6-v2 |
| Vector similarity   | Inner Product / normalized embeddings |

The knowledge base was created from a curated LinkedIn job dataset. Duplicate, promotional/training, senior/management, irrelevant, and similar duplicate job records were filtered before creating the final dataset.

---

## 3. Evaluation Profiles

Five sample student profiles were used for evaluation.

| Student        | Target Role               |
| -------------- | ------------------------- |
| Aarav Sharma   | Machine Learning Intern   |
| Diya Mehta     | Frontend Developer Intern |
| Rohan Kulkarni | Data Science Intern       |
| Ishaan Verma   | Cloud Engineer Intern     |
| Kavya Rao      | Cybersecurity Intern      |

Each profile contains structured candidate information such as target role, skills, education, experience, and projects.

---

## 4. Evaluation Method

For each student profile:

1. Candidate information is converted into a semantic search query.
2. The RAG retriever searches the FAISS vector index.
3. Multiple retrieved chunks belonging to the same job are deduplicated.
4. The corresponding job records are loaded from the structured job dataset.
5. The Job-Resume Matching Agent compares the candidate against each retrieved job.
6. A match score is calculated.
7. Matched and missing skills are identified.
8. Reasoning is generated for each recommendation.
9. The jobs are sorted by match score.
10. The top 5 recommendations are returned.

---

## 5. Evaluation Results

### Overall Results

| Metric                         | Result |
| ------------------------------ | -----: |
| Profiles tested                |      5 |
| Profiles with matching results |      5 |
| Jobs in knowledge base         |    102 |
| Matching results evaluated     |     25 |
| Results per profile            |  Top 5 |
| Minimum match score            |  54.33 |
| Maximum match score            |  80.00 |
| Average match score            |  65.61 |

All five sample profiles successfully produced ranked job recommendations.

---

## 6. Profile-Level Results

### STU001 — Aarav Sharma

**Target Role:** Machine Learning Intern

Top recommendation:

- Data Science Intern — NuvoRetail
- Match Score: **73.00**
- Retrieval Similarity: **0.7868**

The system identified strong matches in Python, Machine Learning, NumPy, Pandas, Scikit-learn and SQL.

Other relevant recommendations included AIML Associate, Python Intern, Artificial Intelligence/Machine Learning Intern, and Data Scientist.

---

### STU002 — Diya Mehta

**Target Role:** Frontend Developer Intern

Top recommendation:

- Software Engineer Intern — Hyperlearn
- Match Score: **75.00**
- Retrieval Similarity: **0.7012**

The system identified strong matches in HTML, CSS and React.

Other relevant recommendations included Web Development Intern roles and a React-based Associate Staff Engineer position.

---

### STU003 — Rohan Kulkarni

**Target Role:** Data Science Intern

Top recommendation:

- Data Science Intern — NuvoRetail
- Match Score: **69.00**
- Retrieval Similarity: **0.8747**

The system identified strong matches in Python, Machine Learning, NumPy, Pandas, Scikit-learn and SQL.

The system also retrieved Python Developer, Associate Data Scientist and Business Analytics roles.

---

### STU004 — Ishaan Verma

**Target Role:** Cloud Engineer Intern

Top recommendation:

- Internship — Python Developer — Spatic
- Match Score: **61.00**
- Retrieval Similarity: **0.7193**

The system identified AWS and Python as matching skills.

The evaluation also retrieved AWS Cloud and Machine Learning internship opportunities, demonstrating that the semantic retrieval pipeline can identify cloud-related opportunities.

However, some lower-ranked results were less relevant to the candidate's target role. This indicates an opportunity for further improvement in role-specific retrieval and ranking.

---

### STU005 — Kavya Rao

**Target Role:** Cybersecurity Intern

Top recommendation:

- Security Operations Center Analyst (Trainee) — Castellum Labs
- Match Score: **80.00**
- Retrieval Similarity: **0.7434**

The system identified strong matches in cybersecurity and Python.

This profile produced the highest match score among the five evaluated profiles.

---

## 7. Observations

The evaluation demonstrates that the system can successfully perform the complete retrieval and matching process on multiple candidate profiles.

### Positive observations

- All 5 profiles produced matching results.
- 25 job recommendations were generated.
- Match scores were generated for the returned jobs.
- The system identified matched skills.
- The system identified missing required skills.
- The system generated natural-language reasoning.
- Results were ranked according to match score.
- The RAG pipeline successfully connected semantic retrieval with structured job matching.

### Areas for improvement

The evaluation also identified opportunities for improving recommendation quality.

Some profiles received semantically related jobs that were not an exact match for their target role. For example, the Cloud Engineer profile received some general Python and analytics-related roles alongside cloud opportunities.

Future improvements can include:

- Giving greater weight to target job title similarity.
- Increasing the importance of required skills during ranking.
- Adding stronger penalties for missing critical skills.
- Improving internship-specific filtering.
- Incorporating location and work-type preferences.
- Expanding the curated job knowledge base.
- Evaluating retrieval and ranking against manually labelled expected results.

These observations are considered part of the evaluation rather than failures of the system.

---

## 8. M2 Component Status

| M2 Component                      | Status       |
| --------------------------------- | ------------ |
| M2.1 Job Dataset & Knowledge Base | ✅ Completed |
| M2.2 RAG Pipeline                 | ✅ Completed |
| M2.3 Job-Resume Matching Agent    | ✅ Completed |
| M2.4 Evaluation                   | ✅ Completed |

### M2 Status: COMPLETED

The M2 implementation successfully demonstrates an end-to-end RAG-based internship retrieval and Job-Resume Matching Agent using a curated job knowledge base and multiple sample student profiles.

The evaluation results provide a baseline for improving recommendation quality in subsequent milestones.

---

## 9. Technology Stack

- **Python**
- **FastAPI**
- **FAISS**
- **Sentence Transformers**
- **all-MiniLM-L6-v2**
- **SQLite**
- **JSON**
- **RAG-based semantic retrieval**
- **Rule/score-based Job-Resume Matching Agent**

---

## 10. Conclusion

M2 successfully establishes the core intelligence required for personalized internship recommendations.

The system can retrieve relevant opportunities from the internship knowledge base, compare them with a structured candidate profile, calculate compatibility scores, identify skill matches and gaps, and provide reasoning for the recommendations.

The next phase will integrate this matching capability into the student-facing Career Companion interface, allowing students to create accounts, upload resumes, view their extracted profiles, and receive personalized internship recommendations.
