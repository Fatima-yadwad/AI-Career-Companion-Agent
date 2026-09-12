# AI Career Companion Agent

> An AI-powered career companion for internship matching, resume intelligence, skill-gap analysis, interview preparation, and personalized career assistance.

## 🚀 Project Overview

**AI Career Companion Agent** is an intelligent multi-agent career platform designed to help students and early-career candidates discover relevant internships and prepare for their careers.

The system combines:

- Resume parsing
- Structured candidate profiles
- Retrieval-Augmented Generation (RAG)
- Semantic job retrieval
- AI-based job-resume matching
- Skill analysis
- Interview preparation
- Career assistance

The current implementation focuses on **Milestone 1 and Milestone 2**, including the candidate profile system, resume intelligence pipeline, internship knowledge base, RAG retrieval, job matching engine, evaluation pipeline, and the Career Companion dashboard.

---

# 🎯 Problem Statement

Students often struggle to:

- Find internships relevant to their skills
- Understand whether their resume matches a job
- Identify missing skills
- Prepare for interviews
- Tailor resumes and applications
- Navigate the internship search process efficiently

Existing job portals primarily provide search and filtering functionality. AI Career Companion aims to provide a more personalized, intelligent workflow by understanding the candidate's profile and resume and comparing them with relevant opportunities.

---

# 💡 Solution

AI Career Companion creates a structured representation of the candidate from their profile and resume.

The system then uses this information to retrieve and rank relevant internship and early-career opportunities.

### Current workflow

```text
Student Profile
       ↓
Resume Upload
       ↓
Resume Parsing
       ↓
Structured Candidate Profile
       ↓
Candidate + Skills + Target Role
       ↓
Semantic RAG Retrieval
       ↓
Job-Resume Matching Engine
       ↓
Ranked Job Recommendations
```

---

# 🏗️ System Architecture

```text
                    AI CAREER COMPANION
                           │
                           ▼
                 ┌───────────────────┐
                 │   React Frontend  │
                 │  Career Dashboard │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │    FastAPI API    │
                 └─────────┬─────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
      ┌────────────┐ ┌────────────┐ ┌─────────────┐
      │  Profile   │ │   Resume   │ │  Matching   │
      │ Management │ │  Analysis  │ │   Engine    │
      └────────────┘ └──────┬─────┘ └──────┬──────┘
                            │                │
                            ▼                ▼
                    ┌──────────────┐ ┌──────────────┐
                    │ Gemini /     │ │ RAG Pipeline │
                    │ Local Parser │ │              │
                    └──────────────┘ └──────┬───────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │ FAISS Vector │
                                    │    Store     │
                                    └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Internship & │
                                    │ Early Career │
                                    │    Jobs      │
                                    └──────────────┘
```

---

# 🧩 Multi-Agent Architecture

The long-term platform is designed around specialized AI agents.

| Agent                     | Responsibility                                 |
| ------------------------- | ---------------------------------------------- |
| Job-Resume Matching Agent | Matches candidates with relevant opportunities |
| Skill Gap Agent           | Identifies missing skills for target roles     |
| Resume Agent              | Improves and tailors resumes                   |
| Cover Letter Agent        | Generates personalized cover letters           |
| Interview Agent           | Provides interview preparation                 |
| Career Assistant          | Provides personalized career guidance          |

### Current implementation

The **Job-Resume Matching workflow is implemented as the primary M2 capability**.

The remaining agents are planned for subsequent milestones.

---

# 📌 Milestone 1 — Candidate & Resume Intelligence

## M1.1 Research

Research covered:

- Internship application workflows
- RAG architecture
- Multi-agent systems
- Resume parsing
- Candidate profile representation
- Technology selection

## M1.2 Architecture

Defined:

- Multi-agent architecture
- Candidate profile schema
- Resume processing pipeline
- RAG-based job retrieval workflow
- Candidate-to-job matching workflow

## M1.3 Student Profile

Implemented:

- Candidate profile creation
- Name
- Email
- Phone
- Location
- Target role
- LinkedIn profile

Profiles are stored in SQLite.

## M1.4 Resume Parsing

Implemented resume upload and extraction for:

- PDF
- DOCX
- TXT

The parser extracts:

- Summary
- Skills
- Education
- Experience
- Projects
- Certifications

### AI extraction

When Gemini is available, the system can use an LLM-based extraction workflow.

A local rule-based extraction fallback is also available so that the application remains functional when an LLM is unavailable.

---

# 🔎 Milestone 2 — RAG & Internship Matching

## M2.1 Internship Dataset

A LinkedIn job dataset was processed and curated for the prototype.

### Final dataset

- **102 job records**
- **20 internship opportunities**
- **78 early-career opportunities**
- **4 trainee opportunities**

The dataset was filtered to focus on relevant technical career opportunities.

No synthetic job records were added.

---

# 🧠 M2.2 RAG Pipeline

The job knowledge base uses Retrieval-Augmented Generation principles.

### Pipeline

```text
Raw Job Dataset
      ↓
Data Cleaning
      ↓
Job Filtering
      ↓
Job Chunking
      ↓
Sentence Transformer Embeddings
      ↓
FAISS Vector Index
      ↓
Semantic Retrieval
      ↓
Candidate-Job Matching
```

### Technology

| Component           | Technology             |
| ------------------- | ---------------------- |
| Embedding Model     | `all-MiniLM-L6-v2`     |
| Embedding Dimension | 384                    |
| Vector Database     | FAISS                  |
| RAG Framework       | Custom Python pipeline |
| Job Storage         | JSON                   |
| Backend             | FastAPI                |
| Database            | SQLite                 |

The current vector store contains:

- **388 indexed vectors**
- **384-dimensional embeddings**

---

# 🎯 M2.3 Job-Resume Matching

The matching engine combines:

- Candidate summary
- Candidate skills
- Target role
- Semantic retrieval similarity
- Job requirements
- Skill overlap

The system retrieves candidate-relevant jobs using semantic search and then calculates a matching score for ranking.

### Matching workflow

```text
Candidate Resume
       ↓
Extracted Skills + Summary
       ↓
Target Role
       ↓
Semantic Query
       ↓
FAISS Retrieval
       ↓
Candidate-Job Scoring
       ↓
Ranked Recommendations
```

---

# 📊 M2.4 Evaluation

The matching pipeline was evaluated using **5 sample candidate profiles**.

### Evaluation results

- Profiles evaluated: **5**
- Jobs in knowledge base: **102**
- Matching results generated: **25**
- Minimum observed match score: **54.33**
- Maximum observed match score: **80.00**
- Average observed match score: **65.61**

The evaluation demonstrates that the complete retrieval and ranking pipeline is operational.

The current evaluation is a **baseline evaluation**, not a claim of production-level accuracy.

### Example

For a Machine Learning candidate, the system retrieved roles including:

- Data Science Intern
- AIML Associate
- Python Intern
- AI/ML Intern
- Data Scientist

This demonstrates semantic retrieval beyond simple keyword matching.

---

# 🖥️ Career Companion Dashboard

The frontend has been redesigned as a professional career platform.

### Current sections

- Dashboard
- My Profile
- My Resume
- Recommended Jobs
- Skill Gap
- Interview Prep
- Applications
- Career Assistant
- Settings

### Current working functionality

✅ Candidate profile creation
✅ Resume upload
✅ Resume analysis
✅ Structured resume extraction
✅ Internship/job retrieval
✅ Semantic matching pipeline
✅ Matching score generation
✅ RAG-powered job search
✅ Professional dashboard UI

Some dashboard sections are currently placeholders for future milestones.

---

# 🛠️ Technology Stack

## Frontend

- React
- Vite
- JavaScript
- CSS

## Backend

- Python
- FastAPI
- SQLite
- Pydantic

## AI / ML

- Google Gemini
- Sentence Transformers
- FAISS
- Semantic Search
- Rule-based fallback extraction

## Document Processing

- PyPDF
- python-docx

## Development

- Git
- GitHub
- VS Code
- PowerShell

---

# 📁 Project Structure

```text
ai-career-companion/
│
├── backend/
│   ├── data/
│   │   ├── career_companion.db
│   │   ├── uploads/
│   │   └── vector_store/
│   │       ├── jobs.index
│   │       └── metadata.json
│   │
│   ├── matching/
│   │   ├── matcher.py
│   │   ├── service.py
│   │   └── job_loader.py
│   │
│   ├── rag/
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── test_retrieval.py
│   │
│   ├── main.py
│   └── .env
│
├── data/
│   ├── raw/
│   └── processed/
│       └── internship_jobs.json
│
├── docs/
│   └── M2_EVALUATION_RESULTS.md
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
│
├── README.md
└── requirements.txt
```

> `.env`, databases, uploaded resumes, and other sensitive/local files should not be committed to GitHub.

---

# ▶️ Running the Project

## 1. Start the backend

Open PowerShell:

```powershell
cd D:\infosys\ai-career-companion
```

Activate the virtual environment if required and start FastAPI:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 2. Start the frontend

Open a second PowerShell window:

```powershell
cd D:\infosys\ai-career-companion\frontend
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔐 Environment Variables

Create:

```text
backend/.env
```

Example:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

**Never commit the real API key to GitHub.**

---

# 📈 Current Development Status

| Milestone                 | Status         |
| ------------------------- | -------------- |
| M1.1 Research             | ✅ Completed   |
| M1.2 Architecture         | ✅ Completed   |
| M1.3 Student Profile      | ✅ Completed   |
| M1.4 Resume Parsing       | ✅ Completed   |
| M2.1 Dataset Preparation  | ✅ Completed   |
| M2.2 RAG Pipeline         | ✅ Completed   |
| M2.3 Job-Resume Matching  | ✅ Completed   |
| M2.4 Evaluation           | ✅ Completed   |
| Professional Dashboard UI | ✅ Implemented |
| Skill Gap Agent           | 🔄 Planned     |
| Resume Agent              | 🔄 Planned     |
| Cover Letter Agent        | 🔄 Planned     |
| Interview Agent           | 🔄 Planned     |
| Career Assistant Agent    | 🔄 Planned     |
| Application Tracking      | 🔄 Planned     |

---

# 🔮 Future Roadmap

### Milestone 3 — Skill Intelligence

- Skill Gap Agent
- Role-specific skill analysis
- Learning recommendations
- Candidate skill progression

### Milestone 4 — Application Assistance

- Resume tailoring
- Cover letter generation
- Job-specific application assistance
- Application tracking

### Milestone 5 — Interview Intelligence

- Personalized interview questions
- Technical interview preparation
- Behavioral interview preparation
- AI interview simulation
- Interview feedback

### Milestone 6 — Career Assistant

- Multi-agent orchestration
- Personalized career recommendations
- Conversational career assistant
- End-to-end internship preparation workflow

---

# 🎓 Project Goal

The ultimate goal is to transform the traditional internship search process into an **AI-assisted career workflow** where a student can:

```text
Upload Resume
      ↓
Understand Skills
      ↓
Discover Relevant Jobs
      ↓
Identify Skill Gaps
      ↓
Improve Resume
      ↓
Generate Cover Letter
      ↓
Prepare for Interview
      ↓
Track Applications
      ↓
Receive Career Guidance
```

---

# 👩‍💻 Project

**AI Career Companion Agent for Internship Matching and Interview Preparation**

Developed as part of the **Infosys Springboard Virtual Internship**.

---

## 📄 Documentation

Detailed M2 evaluation results are available in:

```text
docs/M2_EVALUATION_RESULTS.md
```

The evaluation document contains the dataset statistics, RAG configuration, candidate profiles, matching results, and observations from the baseline evaluation.
