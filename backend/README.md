# AI Career Companion Agent

An AI-powered career assistance platform designed to help students
through the internship and job application journey.

The system builds a structured candidate profile from student-provided
information and resumes, and is designed to provide personalized
career assistance through specialized AI agents.

---

## 1. Project Overview

Students often face difficulties during the internship application
process, including:

- Finding suitable internship opportunities
- Understanding job requirements
- Identifying missing skills
- Improving resumes
- Writing personalized cover letters
- Preparing for interviews
- Tracking applications

The **AI Career Companion Agent** aims to provide a centralized
platform that understands a candidate's profile and assists them
through different stages of the internship application workflow.

The system uses resume parsing, structured candidate profiles,
LLM-based extraction, Retrieval-Augmented Generation (RAG), and a
multi-agent architecture.

---

# 2. Problem Statement

Students need to repeatedly analyze job descriptions, modify resumes,
identify skill gaps, write cover letters, and prepare for interviews.

The goal of this project is to develop an intelligent career companion
that can understand a student's profile and provide personalized
assistance throughout the internship application process.

---

# 3. Milestone 1 – Foundation & Candidate Understanding

Milestone 1 focuses on understanding the candidate and establishing
the foundation of the AI Career Companion system.

### M1.1 – Research & Technical Understanding

The following concepts are being studied and documented:

- Internship application workflows
- Retrieval-Augmented Generation (RAG)
- Multi-agent system design
- Candidate profile modeling
- Resume parsing and information extraction

### M1.2 – System Architecture

The system architecture defines:

- Student/User Interface
- Backend/API Layer
- Candidate Profile
- Resume Upload and Storage
- Resume Parsing Module
- Database
- LLM Integration
- Job-Posting Knowledge Base
- RAG Pipeline
- AI Agent Layer
- Application Tracking Module
- Communication/Data Flow

### M1.3 – Student Profile Module

Implemented functionality:

- Student profile creation
- Email validation
- Candidate information storage
- Resume upload
- Resume metadata storage
- SQLite database integration

### M1.4 – Resume Parsing & Extraction

Implemented functionality:

- PDF resume parsing
- DOCX resume parsing
- TXT resume parsing
- Text extraction
- Structured skill extraction
- Education extraction
- Experience extraction
- Project extraction
- Certification extraction
- LLM-based extraction
- Local fallback extraction

---

# 4. Current System Workflow

```text
                 Student / User
                       |
                       v
              Create Candidate Profile
                       |
                       v
                 Upload Resume
                       |
                       v
              Resume File Storage
                       |
                       v
                Resume Parser
                       |
                       v
                Extract Resume Text
                       |
                       v
             Structured Extraction
                       |
              ┌────────┴────────┐
              |                 |
              v                 v
        OpenAI LLM         Local Fallback
              |                 |
              └────────┬────────┘
                       |
                       v
             Structured Candidate Data
                       |
                       v
                 SQLite Database
```
