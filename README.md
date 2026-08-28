# 🤖 AI Career Companion Agent

> **AI-powered career assistance for internship matching, resume analysis, skill-gap identification, and interview preparation.**

The **AI Career Companion Agent** is an AI-based platform designed to help students throughout the internship application and preparation process.

The system analyzes a student's profile and resume, extracts structured information such as skills, education, experience, projects, and certifications, and uses this information as the foundation for personalized career guidance.

The planned system combines **React, FastAPI, SQLite, Gemini/LLM, Retrieval-Augmented Generation (RAG), and specialized AI agents** to create an intelligent career-support platform.



## 🎯 Project Objective

Finding and preparing for internships can be challenging for students because every opportunity may have different requirements.

Students often need to:

* Search for suitable internships
* Understand job requirements
* Compare their skills with job requirements
* Identify missing skills
* Customize their resumes
* Write cover letters
* Prepare for interviews
* Track their applications
* Make informed career decisions

The goal of the **AI Career Companion Agent** is to bring these activities together into one platform and provide personalized assistance based on the student's profile and resume.



## 🏗️ System Architecture

The proposed system follows a layered architecture:

```text
Student
   ↓
React Frontend
   ↓
FastAPI Backend
   ↓
Profile + Resume Database
   ↓
Resume Parser
   ↓
LLM / Gemini
   ↓
RAG Knowledge Base
   ↓
6 Specialized Agents
   ↓
Career Recommendations
```

### Architecture Flow

1. **Student** interacts with the application.
2. **React Frontend** provides the user interface.
3. **FastAPI Backend** handles API requests, validation, and system coordination.
4. **Profile + Resume Database** stores candidate information and resume metadata.
5. **Resume Parser** extracts text from uploaded resumes.
6. **Gemini/LLM** converts unstructured resume text into structured information.
7. **RAG Knowledge Base** provides relevant internship and career information.
8. **Six Specialized AI Agents** perform different career-support tasks.
9. **Career Recommendations** are generated based on the student's profile and relevant information.



## 🧩 Core Components

| Component              | Purpose                                               |
| ---------------------- | ----------------------------------------------------- |
| **React + Vite**       | Student-facing web interface                          |
| **FastAPI**            | Backend API and system coordination                   |
| **SQLite**             | Candidate and resume metadata storage for Milestone 1 |
| **Resume Parser**      | Extracts text from PDF, DOCX, and TXT resumes         |
| **Gemini / LLM**       | Extracts structured information from resume text      |
| **RAG Knowledge Base** | Retrieves relevant internship and career information  |
| **AI Agent Layer**     | Provides specialized career assistance                |
| **Local File Storage** | Stores uploaded resumes during development            |



# 📄 Resume Processing Pipeline

The initial system focuses on transforming an uploaded resume into a structured candidate profile.

```text
Resume Upload
      ↓
File Validation
      ↓
Resume Parser
      ↓
Extracted Text
      ↓
Gemini / LLM
      ↓
Structured Resume JSON
      ↓
Database
      ↓
AI Career Agents
```

The system extracts information including:

* Summary
* Skills
* Education
* Experience
* Projects
* Certifications

This structured information can then be reused by the different AI agents.



# 🗄️ Database Design

The initial database contains two primary entities:

```text
┌──────────────────────┐
│       PROFILES       │
├──────────────────────┤
│ PK id                │
│ full_name            │
│ email                │
│ phone                │
│ location             │
│ target_role          │
│ linkedin_url         │
│ created_at           │
└──────────┬───────────┘
           │
           │ 1 : N
           ▼
┌──────────────────────┐
│       RESUMES        │
├──────────────────────┤
│ PK id                │
│ FK profile_id        │
│ filename             │
│ file_path            │
│ file_type            │
│ size_bytes           │
│ uploaded_at          │
│ extraction_json      │
│ extraction_method    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  STRUCTURED RESUME   │
├──────────────────────┤
│ Summary              │
│ Skills               │
│ Education            │
│ Experience           │
│ Projects             │
│ Certifications       │
└──────────────────────┘
```

### Profiles

Stores basic student information such as:

* Full name
* Email
* Phone
* Location
* Target role
* LinkedIn URL
* Profile creation date

### Resumes

Stores information about uploaded resumes including:

* Filename
* File path
* File type
* File size
* Upload date
* Extracted JSON
* Extraction method

A single student profile can have multiple resumes, giving a **one-to-many (1:N)** relationship.



# 🧠 Retrieval-Augmented Generation (RAG)

**Retrieval-Augmented Generation (RAG)** will be used in later milestones to provide the AI system with relevant external information.

The knowledge base can contain:

* Internship job descriptions
* Required skills
* Eligibility criteria
* Company information
* Interview preparation resources
* Career guidance resources

### RAG Workflow

```text
Job Postings / Career Resources
              ↓
        Document Collection
              ↓
          Text Chunking
              ↓
          Embeddings
              ↓
        Vector Database
              ↓
       Semantic Retrieval
              ↓
       Relevant Context
              ↓
          LLM / Agent
              ↓
        AI Response
```

Potential technologies for the future RAG layer include:

* **Chroma**
* **pgvector**

RAG will allow the system to retrieve relevant information instead of depending only on the general knowledge of the language model.



# 🤖 Six Specialized AI Agents

The planned system contains six specialized AI agents.

| Agent                            | Responsibility                                                                         |
| -------------------------------- | -------------------------------------------------------------------------------------- |
| 🎯 **Job–Resume Matching Agent** | Compares the student's profile with internship requirements and provides a match score |
| 📚 **Skill Gap Agent**           | Identifies missing or weak skills and recommends learning priorities                   |
| 📝 **Resume Agent**              | Suggests improvements to the resume for a selected internship                          |
| ✉️ **Cover Letter Agent**        | Generates personalized cover-letter drafts                                             |
| 🎤 **Interview Agent**           | Generates interview questions and provides practice feedback                           |
| 💼 **Career Assistant**          | Handles general internship and career-related questions                                |

The agents will use the structured candidate profile and, where required, information retrieved from the RAG knowledge base.



# 🔄 Multi-Agent Workflow

```text
                    Student Request
                          │
                          ▼
                   ┌──────────────┐
                   │ Orchestrator │
                   └──────┬───────┘
                          │
        ┌─────────────────┼──────────────────┐
        │        │        │        │         │
        ▼        ▼        ▼        ▼         ▼
     Matching  Skill    Resume   Cover     Interview
      Agent    Gap      Agent    Letter      Agent
               Agent             Agent
        │        │        │        │         │
        └────────┴────────┴────────┴─────────┘
                          │
                          ▼
                 Career Assistant
                          │
                          ▼
                Career Recommendations
```

The orchestrator/backend will determine which specialized agent should handle a particular student request.



# 🛠️ Technology Stack

| Layer                | Technology          |
| -------------------- | ------------------- |
| **Frontend**         | React + Vite        |
| **Backend**          | FastAPI + Python    |
| **Database**         | SQLite              |
| **Resume Parsing**   | PyPDF + python-docx |
| **LLM**              | Gemini              |
| **File Storage**     | Local Storage       |
| **Future RAG Store** | Chroma / pgvector   |
| **Version Control**  | Git + GitHub        |



# 📁 Project Structure

```text
AI-Career-Companion-Agent/
│
├── backend/
│   ├── main.py
│   ├── README.md
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── README.md
│
├── docs/
│   ├── Research-and-Technical-Understanding.pdf
│   ├── System-Architecture.pdf
│   ├── architecture-diagram.png
│   ├── database schema.jpeg
│   └── work flow diagram.jpeg
│
└── README.md
```



# 🚧 Milestone 1

The first milestone focuses on establishing the candidate-profile and resume-processing foundation.

### Completed / Planned Foundation

* [x] Project repository setup
* [x] Frontend project setup
* [x] Backend project setup
* [x] Initial system architecture
* [x] Database schema design
* [x] Research and technical understanding documentation
* [ ] Student profile creation
* [ ] Profile validation
* [ ] Resume upload
* [ ] Resume metadata storage
* [ ] PDF resume parsing
* [ ] DOCX resume parsing
* [ ] TXT resume processing
* [ ] Gemini-based structured extraction
* [ ] Structured resume storage

### Future Milestones

* [ ] RAG knowledge base
* [ ] Internship/job data integration
* [ ] Job–Resume Matching Agent
* [ ] Skill Gap Agent
* [ ] Resume Agent
* [ ] Cover Letter Agent
* [ ] Interview Agent
* [ ] Career Assistant
* [ ] Application tracking
* [ ] Personalized career recommendations



# 📚 Documentation

The project documentation is available in the [`docs`](./docs) directory.

### Research and Technical Understanding

Contains research on:

* Internship application workflow
* Retrieval-Augmented Generation
* Multi-agent systems
* System architecture
* Database design
* Technology selection
* Milestone 1 scope

### System Architecture

Contains the detailed architecture and workflow of the proposed system.



# 🎯 Expected Outcome

The final system aims to provide students with a single AI-powered platform for internship preparation.

The platform will eventually support:

```text
Student Profile
      ↓
Resume Analysis
      ↓
Internship Matching
      ↓
Skill Gap Identification
      ↓
Resume Improvement
      ↓
Cover Letter Generation
      ↓
Interview Preparation
      ↓
Career Guidance
```

This approach is intended to make internship preparation more organized, personalized, and efficient.



# 🔮 Future Enhancements

Possible future improvements include:

* Integration with live internship/job sources
* PostgreSQL for scalable database storage
* Cloud-based resume storage
* Advanced semantic search
* Personalized learning recommendations
* Mock interview sessions
* Application tracking dashboard
* Analytics on application progress
* Authentication and user accounts
* Deployment using cloud infrastructure
* Additional specialized career agents



# 📌 Conclusion

The **AI Career Companion Agent** provides a structured approach to helping students navigate the internship process.

The initial milestone establishes the core candidate-profile and resume-processing pipeline. The system uses **React and Vite** for the frontend, **FastAPI and Python** for the backend, **SQLite** for initial data storage, and **Gemini/LLM** technology for structured resume extraction.

The future integration of **RAG** will allow the system to retrieve relevant internship and career information, while the **six specialized AI agents** will provide personalized assistance for job matching, skill-gap analysis, resume improvement, cover letters, interview preparation, and general career guidance.

The architecture is designed to be modular and extensible so that additional AI capabilities, data sources, and production infrastructure can be added in future milestones.

## 👩‍💻 Project

**AI Career Companion Agent**

**Developed as part of the Infosys Internship Project**

**Repository:** [AI-Career-Companion-Agent](https://github.com/Fatima-yadwad/AI-Career-Companion-Agent)
