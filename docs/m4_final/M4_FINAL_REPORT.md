# AI Career Companion Agent

## Milestone 4 — Final Technical Report

**Project:** AI Career Companion Agent
**Milestone:** M4 — Application Management, End-to-End Validation, Optimization & Final Documentation
**Technology:** Python, FastAPI, SQLite, FAISS, Sentence Transformers, Gemini API
**Status:** M4 implementation and validation completed

---

# 1. Executive Summary

The AI Career Companion Agent is an AI-assisted career platform designed to help students discover relevant internship opportunities, understand skill gaps, prepare application materials, prepare for interviews, track applications, and receive contextual career guidance.

The project combines:

- Resume processing
- Semantic job retrieval
- Job-resume matching
- Skill-gap analysis
- Resume customization
- Cover-letter generation
- Interview preparation
- Mock interview evaluation
- Conversational career assistance
- Application tracking

Milestone 4 focuses on integrating these capabilities into a complete student workflow, implementing application tracking and management, validating the integrated system through end-to-end testing, measuring performance, and documenting the technical architecture.

The completed M4 validation recorded:

```text id="x8h2a1"
80 tests executed
80 passed
0 failed
0 blocked
```

The Application Tracker section achieved:

```text id="v5n3d8"
16/16 PASS
```

The separate M4.3 performance test recorded:

```text id="r4c9m2"
9 successful operations
0 failed operations
124.909 seconds total measured workflow time
M4.3 PERFORMANCE TEST PASSED
```

These results represent the tested local development environment and should not be interpreted as production-scale performance guarantees.

---

# 2. Introduction

Students searching for internships often need to perform multiple disconnected activities:

1. Find suitable opportunities.
2. Understand job requirements.
3. Compare their skills against those requirements.
4. Customize their resume.
5. Prepare a cover letter.
6. Prepare for interviews.
7. Track submitted applications.
8. Remember deadlines and follow-ups.
9. Obtain guidance throughout the process.

Traditional job-search workflows often require students to manually perform these tasks across different platforms.

The AI Career Companion Agent brings these activities into a single workflow by combining retrieval, deterministic matching, specialized AI agents, and application management.

The system is designed as a career-support tool rather than simply a job-search interface.

---

# 3. Problem Statement

Students can find it difficult to determine which internships match their existing skills and what they need to improve before applying.

Even after identifying an opportunity, students may need to manually:

- Compare their resume with the job description.
- Identify missing skills.
- Rewrite their resume.
- Prepare a cover letter.
- Research interview topics.
- Practice interview answers.
- Track application progress.
- Remember deadlines and follow-ups.

The project addresses this problem by providing an integrated AI-assisted workflow that connects job discovery, candidate analysis, application preparation, interview preparation, career guidance, and application tracking.

---

# 4. Project Objectives

The main objectives are:

- Build a semantic internship/job retrieval system.
- Develop a job-resume matching pipeline.
- Identify candidate skill gaps.
- Generate grounded application materials.
- Provide interview preparation.
- Support mock interview evaluation.
- Provide profile-aware conversational career guidance.
- Implement application tracking and management.
- Validate the complete workflow through automated testing.
- Measure system performance.
- Identify optimization opportunities for future scaling.
- Maintain grounded outputs without inventing unsupported candidate information.

---

# 5. Functional Requirements

The system supports the following major capabilities.

## 5.1 Candidate Profile

Students can maintain profile information including:

- Full name
- Email
- Phone
- Location
- Target role
- LinkedIn URL

## 5.2 Resume Processing

The system supports:

- PDF resumes
- DOCX resumes
- TXT resumes

Resume content is extracted and converted into structured candidate information.

The extracted structure can include:

- Summary
- Skills
- Education
- Experience
- Projects
- Certifications

## 5.3 Internship Retrieval

Students can search the internship knowledge base using natural-language queries.

The RAG system retrieves semantically relevant job information.

## 5.4 Job-Resume Matching

The matching layer evaluates candidate-job compatibility using:

- Required skills
- Preferred skills
- Project relevance
- Education
- Experience
- Qualifications

## 5.5 Skill Gap Analysis

The Skill Gap Agent identifies:

- Matched skills
- Missing skills
- Critical gaps
- Preferred gaps
- Experience gaps
- Qualification gaps
- Recommendations

## 5.6 Application Customization

The Application Agent supports:

- Tailored resume generation
- Cover-letter generation

## 5.7 Interview Preparation

The Interview Agent provides questions and preparation guidance for:

- Technical interviews
- Resume questions
- Project questions
- Role-specific questions
- HR questions

The system also supports mock-interview answer evaluation.

## 5.8 Career Assistant

The Career Assistant provides contextual career guidance using candidate, job, skill-gap, and recent conversation information.

## 5.9 Application Tracking

Students can:

- Add applications
- Update applications
- Search applications
- Filter applications
- Track deadlines
- Track interviews
- Record follow-ups
- Store notes
- Store generated resumes and cover letters
- View application dashboard metrics
- Delete applications

---

# 6. System Architecture

The application uses a layered architecture.

```text id="q1s7n4"
                    Student
                       |
                       v
                FastAPI REST API
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
     Profile       Job Search     Applications
        |              |
        v              v
     Resume        RAG Retriever
     Processing         |
        |               v
        |          FAISS Index
        |               |
        +-------+-------+
                |
                v
        Candidate / Job Context
                |
     +----------+----------+
     |          |          |
     v          v          v
 Skill Gap   Application  Interview
   Agent       Agent       Agent
     |          |          |
     +----------+----------+
                |
                v
        Career Assistant
                |
                v
        SQLite Persistence
```

The actual implementation separates semantic retrieval from deterministic matching and from generative agent functionality.

---

# 7. Technology Stack

| Layer                 | Technology                 |
| --------------------- | -------------------------- |
| Programming language  | Python                     |
| API framework         | FastAPI                    |
| Database              | SQLite                     |
| Vector search         | FAISS                      |
| Embeddings            | Sentence Transformers      |
| Embedding model       | `all-MiniLM-L6-v2`         |
| Embedding dimension   | 384                        |
| LLM integration       | Gemini API                 |
| Resume PDF extraction | pypdf                      |
| DOCX processing       | python-docx                |
| Testing               | Pytest                     |
| API testing           | FastAPI TestClient / HTTPX |
| Data format           | JSON                       |
| Vector metadata       | JSON                       |

---

# 8. Knowledge Base

The internship knowledge base contains curated internship/job records.

The current documented dataset contains:

```text id="p3a6j0"
102 jobs
388 semantic chunks
388 vectors
384-dimensional embeddings
```

The dataset was prepared during the earlier project milestone and is used as the source knowledge base for semantic job retrieval.

The knowledge base excludes unsuitable records according to the project's earlier curation process, including duplicate, promotional, senior/management, training, and irrelevant records.

---

# 9. RAG Pipeline

The Retrieval-Augmented Generation pipeline uses the following process:

```text id="a7d5r2"
Job Dataset
    |
    v
Section-Based Chunking
    |
    v
Sentence Transformer Embeddings
    |
    v
Normalized 384-D Vectors
    |
    v
FAISS IndexFlatIP
    |
    v
Semantic Query
    |
    v
Retrieved Chunks
    |
    v
Job-Level Deduplication
    |
    v
Structured Job Records
    |
    v
Matching / Agents
```

---

# 10. RAG Chunking Strategy

Each job can be divided into semantic sections:

- Job description
- Responsibilities
- Required skills
- Preferred skills
- Qualifications
- Experience requirements
- Education requirements

Each chunk retains job metadata.

This allows the retrieval system to identify the relevant part of a job posting rather than representing the entire posting as one large vector.

---

# 11. Embedding and Vector Search

The system uses:

```text id="m8x1r4"
Sentence Transformers
all-MiniLM-L6-v2
384-dimensional embeddings
```

Embeddings are normalized before indexing.

The FAISS index uses:

```text id="b7q4s9"
IndexFlatIP
```

Since the embeddings are normalized, inner product corresponds to cosine similarity.

The index and metadata are loaded during RAG initialization.

An integrity check verifies that the number of FAISS vectors matches the metadata record count.

---

# 12. Retrieval Optimization

The matching service retrieves more candidates than the final requested number and then performs downstream matching.

The retrieval count follows:

```text id="c2p6v8"
min(max(top_k * 3, 5), 20)
```

This provides additional candidate jobs for deterministic compatibility scoring while keeping the retrieval set bounded.

Retrieved chunks are then deduplicated by `job_id`.

This prevents multiple chunks from the same job from unnecessarily occupying the candidate set.

---

# 13. Job-Resume Matching Architecture

The Job-Resume Matching Agent is implemented as a RAG retrieval plus deterministic scoring pipeline.

The process is:

```text id="s4j8k1"
Candidate Profile
      |
      v
Semantic Query
      |
      v
FAISS Retrieval
      |
      v
Candidate Jobs
      |
      v
Deterministic Compatibility Scoring
      |
      v
Sorted Match Results
```

The final result includes:

- Match score
- Matched skills
- Missing skills
- Component scores
- Retrieval similarity
- Reasoning

---

# 14. Matching Score

The current weighted score is:

| Component         |   Weight |
| ----------------- | -------: |
| Required skills   |      40% |
| Preferred skills  |      15% |
| Project relevance |      15% |
| Education         |      10% |
| Experience        |      10% |
| Qualifications    |      10% |
| **Total**         | **100%** |

This deterministic scoring approach provides a reproducible compatibility calculation.

The semantic retrieval similarity is recorded separately and is not directly included in the current weighted score.

---

# 15. Skill Normalization

The matching system normalizes common skill aliases.

Examples include:

| Alias    | Normalized value            |
| -------- | --------------------------- |
| ML       | Machine Learning            |
| DL       | Deep Learning               |
| AI       | Artificial Intelligence     |
| CV       | Computer Vision             |
| NLP      | Natural Language Processing |
| JS       | JavaScript                  |
| TS       | TypeScript                  |
| postgres | PostgreSQL                  |
| sklearn  | scikit-learn                |

This reduces mismatches caused by common terminology variations.

---

# 16. Skill Gap Agent

The Skill Gap Agent compares candidate skills against the selected job.

The deterministic foundation calculates:

- Required skill matches
- Preferred skill matches
- Missing required skills
- Missing preferred skills
- Overall skill-match percentage

The agent can then use the LLM to generate explanations and recommendations.

The system also provides deterministic fallback behavior when LLM generation is unavailable.

A core grounding rule is that the agent must not invent candidate skills or experience.

---

# 17. Application Agent

The Application Agent provides two main functions.

### Resume customization

The agent can generate:

- Professional summary
- Highlighted skills
- Projects
- Experience
- Education
- Certifications
- Suggested keywords
- Customization strategy

### Cover letter

The agent can generate:

- Subject
- Salutation
- Opening
- Skills alignment
- Project alignment
- Company fit
- Closing
- Sign-off
- Full letter

The prompts explicitly prohibit unsupported claims such as invented employers, degrees, certifications, projects, metrics, and achievements.

Deterministic fallback generation is available when LLM generation fails.

---

# 18. Interview Agent

The Interview Agent generates preparation material from the candidate and selected job.

Question categories include:

- Technical
- Resume
- Project
- Role-specific
- HR

The system also supports mock-interview answer evaluation.

Evaluation can consider:

- Technical understanding
- Relevance
- Clarity
- Completeness
- Project understanding

LLM evaluation has deterministic fallback behavior.

---

# 19. Career Assistant

The Career Assistant provides conversational career guidance.

The contextual information can include:

- Candidate name
- Target role
- Skills
- Projects
- Education
- Selected job
- Required skills
- Preferred skills
- Skill-gap information
- Recent conversation history

The implementation limits the included conversation history to recent turns to avoid unnecessarily large prompts.

The system is instructed to remain grounded in the candidate's actual information.

---

# 20. Application Tracking & Management

The M4.1 Application Tracker adds persistent application management.

Applications are stored in SQLite and associated with a candidate profile.

Supported information includes:

- Company
- Job title
- Job description
- Application date
- Deadline
- Status
- Interview date
- Interview status
- Notes
- Follow-up date
- Customized resume
- Cover letter

---

# 21. Application Status Lifecycle

The supported statuses are:

1. Saved
2. Planning to apply
3. Applied
4. Application under review
5. Shortlisted
6. Interview scheduled
7. Interview completed
8. Offer received
9. Rejected
10. Withdrawn

The backend validates status values before saving them.

---

# 22. Application Tracker APIs

| Method | Endpoint                                               | Purpose              |
| ------ | ------------------------------------------------------ | -------------------- |
| POST   | `/profiles/{profile_id}/applications`                  | Create application   |
| GET    | `/profiles/{profile_id}/applications`                  | List/search/filter   |
| GET    | `/profiles/{profile_id}/applications/dashboard`        | Dashboard            |
| GET    | `/profiles/{profile_id}/applications/{application_id}` | Retrieve application |
| PUT    | `/profiles/{profile_id}/applications/{application_id}` | Update application   |
| DELETE | `/profiles/{profile_id}/applications/{application_id}` | Delete application   |

The application list endpoint supports filtering by company, role, status, application date, deadline, and general search.

---

# 23. Application Dashboard

The dashboard provides:

- Total applications
- Active applications
- Upcoming deadlines
- Scheduled interviews
- Offers received
- Rejected applications

It also provides lists for:

- Upcoming deadlines
- Recent applications
- Upcoming interviews
- Applications needing follow-up

This provides the student with a consolidated view of their current application activity.

---

# 24. Duplicate Application Protection

When an application includes a `job_id`, the backend checks whether that job has already been added for the same profile.

If an existing application is found, creation is rejected.

This protects application data from accidental duplicate records.

The duplicate-protection behavior was also included in the M4 E2E validation.

---

# 25. Grounding and Hallucination Control

Grounding is a major design principle across the AI components.

The system instructs agents to use only candidate information available in the profile/resume context.

The agents should not invent:

- Skills
- Employers
- Projects
- Degrees
- Certifications
- Achievements
- Metrics
- Work experience

For missing information, the system can use statements indicating that evidence is unavailable instead of fabricating information.

This is particularly important for career documents because generated false claims could make a student's application inaccurate.

---

# 26. Fallback Architecture

The project includes deterministic fallback behavior for several AI-assisted operations.

The general flow is:

```text id="d8m3q1"
Request
   |
   v
Agent
   |
   v
LLM Request
 /       \
Success   Failure
 |           |
 v           v
LLM       Deterministic
Output      Fallback
 \           /
  \         /
   v       v
 API Response
```

This improves resilience when the external model service is unavailable or rate-limited.

Fallback behavior is currently available across several major agent functions.

---

# 27. M4 Testing Strategy

Testing was divided into functional, integration, consistency, error-handling, and performance categories.

The main test suite is:

```text id="x4p7z2"
backend/test_m4_e2e.py
```

Performance testing is implemented separately in:

```text id="h6n1w9"
backend/test_m43_performance.py
```

---

# 28. M4 E2E Test Results

The recorded E2E test execution achieved:

```text id="n2c7a5"
Total Tests Executed : 80
PASS                 : 80
FAIL                 : 0
BLOCKED              : 0
```

The overall test execution took approximately:

```text id="y9r3k5"
191.75 seconds
```

Pytest reported the test suite as passed.

---

# 29. E2E Test Breakdown

| Area                      | Result |
| ------------------------- | -----: |
| Profile                   |    5/5 |
| Resume                    |    4/4 |
| RAG                       |    5/5 |
| Matching                  |    4/4 |
| Skill Gap                 |    5/5 |
| Application Customization |    4/4 |
| Interview                 |    5/5 |
| Career Assistant          |    5/5 |
| Application Tracker       |  16/16 |
| Error / Edge Cases        |    9/9 |
| Multi-Agent Consistency   |    4/4 |
| Overall E2E               |  80/80 |

All recorded checks passed.

---

# 30. Multi-Agent Consistency

The M4 tests include checks across the specialized AI components.

The consistency tests achieved:

```text id="t3v8q4"
4/4 PASS
```

The purpose is to verify that downstream agents receive compatible candidate and job information and do not introduce contradictions.

The major agent components include:

- Skill Gap Agent
- Application Agent
- Interview Agent
- Career Assistant

The agents share grounded candidate/job context rather than independently generating unsupported candidate facts.

---

# 31. Error and Edge-Case Testing

The error/edge test section achieved:

```text id="j7p2m8"
9/9 PASS
```

The tests cover invalid or incomplete scenarios and verify that the API returns controlled responses.

Application-specific validation includes:

- Invalid statuses
- Duplicate applications
- Missing applications
- Missing profiles
- Profile/application relationship validation

---

# 32. M4.3 Performance Results

The performance test measured the major workflow operations.

Recorded timings:

| Operation             |     Time |
| --------------------- | -------: |
| Health                |  0.010 s |
| RAG job search        |  0.068 s |
| Job matching          |  2.435 s |
| Skill gap             | 24.980 s |
| Resume customization  | 24.017 s |
| Cover letter          | 25.674 s |
| Interview preparation | 24.502 s |
| Career Assistant      | 23.224 s |

The overall measured results were:

```text id="e6q1t7"
Successful operations : 9
Failed operations     : 0
Total time            : 124.909 s
Average               : 15.614 s
Median                : 23.621 s
Fastest               : 0.010 s
Slowest               : 25.674 s
```

The test concluded with:

```text id="r1c5v9"
M4.3 PERFORMANCE TEST PASSED
```

---

# 33. Performance Analysis

The measurements show that the system has different latency characteristics depending on the operation.

### RAG

RAG retrieval was measured at:

```text id="s2k7a4"
0.068 seconds
```

This is substantially lower than the generation-heavy operations.

### Matching

Job matching took:

```text id="m3v8q1"
2.435 seconds
```

The deterministic matching layer is therefore considerably faster than the generation-heavy agent operations.

### Generation-heavy operations

Skill Gap, Resume Customization, Cover Letter, Interview Preparation, and Career Assistant took approximately 23–26 seconds in the recorded run.

These operations involve LLM-dependent processing and therefore represent the primary latency area in the current workflow.

---

# 34. LLM Quota and Fallback Observation

During the recorded performance test, the configured Gemini API model had exhausted its available quota.

Some LLM operations therefore logged quota-related failures and used deterministic fallback behavior.

The API operations nevertheless completed successfully for the performance test.

This confirms the usefulness of the fallback architecture, but the recorded timings should not be treated as measurements of successful LLM-only generation latency.

---

# 35. Optimization Measures

The current system contains several optimization mechanisms.

### RAG

- Section-based chunks
- Normalized embeddings
- FAISS vector index
- Bounded retrieval
- Job-level deduplication

### Matching

- Deterministic scoring
- Skill normalization
- Weighted compatibility components
- Structured job reconstruction

### Agents

- Condensed candidate/job context
- Limited recent conversation history
- Grounded prompts
- Deterministic fallbacks

### Application Tracking

- SQLite indexes
- Profile-level queries
- Status filtering
- Deadline filtering
- Duplicate protection

---

# 36. Current Limitations

The system has several known limitations.

## 36.1 Knowledge-base size

The current knowledge base contains 102 jobs. Larger-scale testing would be required to understand production retrieval behavior.

## 36.2 LLM dependency

LLM-dependent operations can experience external latency, quota limitations, or service availability issues.

## 36.3 Deterministic fallback quality

Fallback responses provide resilience but may not have the same richness as successful LLM responses.

## 36.4 Experience scoring

The current deterministic experience component provides a relatively simple compatibility signal and does not fully estimate detailed years of experience.

## 36.5 Qualification scoring

Qualification matching currently uses lightweight text-based matching rather than deep semantic qualification analysis.

## 36.6 Performance environment

The reported performance measurements were obtained in the local development environment.

They should not be treated as production-scale throughput or latency guarantees.

## 36.7 Automated reminders

The current tracker identifies upcoming deadlines, interviews, and follow-up records but future versions can introduce scheduled notification mechanisms.

---

# 37. Future Scope

Potential future improvements include:

### RAG

- Larger internship knowledge base
- Better retrieval evaluation datasets
- Approximate nearest-neighbor indexing
- Hybrid lexical + semantic retrieval
- Retrieval reranking
- Retrieval caching

### Matching

- Experience-duration extraction
- Required-vs-preferred priority refinement
- Industry/role compatibility
- Location preferences
- Work-mode preferences
- More detailed education matching

### Agents

- Improved grounding evaluation
- Structured output validation
- Better fallback templates
- Response caching
- Prompt optimization
- Token-usage monitoring

### Application Tracker

- Calendar integration
- Automated deadline reminders
- Interview reminders
- Follow-up notifications
- Application history
- Status transition history
- Analytics dashboards

### Infrastructure

- Async background jobs
- Distributed workers
- Production vector database
- Database scaling
- API load balancing
- CI/CD regression testing
- Monitoring and observability

---

# 38. Security and Data Considerations

The application associates data with candidate profiles.

The backend performs profile-access checks when an authenticated user context is available.

Application queries are scoped using `profile_id`.

This is important because candidate information can include personal and career-related data.

Future production deployment should additionally include:

- Secure secret management
- HTTPS
- Strong authentication
- Authorization policies
- Database backups
- Encryption where appropriate
- Audit logging
- Data-retention policies
- Secure file-storage controls

---

# 39. End-to-End Student Workflow

The final intended student workflow is:

```text id="n4w8s1"
Create Profile
      |
      v
Upload Resume
      |
      v
Parse Resume
      |
      v
Search Internships
      |
      v
Retrieve Relevant Jobs
      |
      v
Calculate Job Match
      |
      v
Analyze Skill Gap
      |
      +----------------------+
      |                      |
      v                      v
Customize Resume       Generate Cover Letter
      |                      |
      +----------+-----------+
                 |
                 v
        Prepare for Interview
                 |
                 v
          Mock Interview
                 |
                 v
       Track Application
                 |
        +--------+--------+
        |        |        |
        v        v        v
     Status   Deadline  Interview
        |        |        |
        +--------+--------+
                 |
                 v
          Career Assistant
```

This workflow connects the major project components into a single student-centered process.

---

# 40. Project Achievement Summary

The implemented system now provides a combined career-support workflow covering:

| Capability                | Implementation   |
| ------------------------- | ---------------- |
| Candidate profile         | Implemented      |
| Resume upload             | Implemented      |
| Resume parsing            | Implemented      |
| Semantic job retrieval    | Implemented      |
| Job-resume matching       | Implemented      |
| Skill-gap analysis        | Implemented      |
| Resume customization      | Implemented      |
| Cover-letter generation   | Implemented      |
| Interview preparation     | Implemented      |
| Mock interview evaluation | Implemented      |
| Career Assistant          | Implemented      |
| Application tracking      | Implemented      |
| Application dashboard     | Implemented      |
| E2E testing               | Implemented      |
| Performance testing       | Implemented      |
| Deterministic fallback    | Implemented      |
| Technical documentation   | Completed for M4 |

---

# 41. Evidence Summary

The major recorded M4 evidence is:

### Functional validation

```text id="w2r5h8"
80/80 E2E tests passed
0 failures
0 blocked
```

### Application Tracker

```text id="c6n1p4"
16/16 tests passed
```

### Multi-Agent Consistency

```text id="q9v3k7"
4/4 tests passed
```

### Error / Edge Cases

```text id="j1m6s8"
9/9 tests passed
```

### Performance

```text id="a8r2d5"
9 successful operations
0 failures
124.909 seconds measured workflow time
M4.3 PERFORMANCE TEST PASSED
```

These values are based on the recorded local test executions.

---

# 42. Technical Documentation Produced

The M4 final documentation set includes:

```text id="f5k8p2"
docs/m4_final/
|
+-- M4_TECHNICAL_ARCHITECTURE.md
+-- M4_AGENT_RESPONSIBILITIES.md
+-- M4_RAG_AND_KNOWLEDGE_BASE.md
+-- M4_APPLICATION_TRACKER.md
+-- M4_TESTING_AND_EVALUATION.md
+-- M4_OPTIMIZATION_AND_PERFORMANCE.md
+-- M4_FINAL_REPORT.md
```

Each supporting document provides additional detail for its corresponding M4 requirement.

---

# 43. Conclusion

The AI Career Companion Agent has evolved into an integrated career-support workflow combining semantic retrieval, deterministic candidate-job matching, specialized AI agents, application generation, interview preparation, conversational assistance, and application management.

Milestone 4 completed the application-tracking layer and validated the integration of the major components.

The recorded M4 E2E execution achieved:

```text id="z7q4m1"
80/80 PASS
```

The Application Tracker achieved:

```text id="p2n8c5"
16/16 PASS
```

The performance evaluation achieved:

```text id="u6r3k9"
9 successful operations
0 failures
M4.3 PERFORMANCE TEST PASSED
```

The project now has a documented technical architecture, RAG and knowledge-base description, agent responsibility specification, application-tracker documentation, testing/evaluation results, optimization/performance analysis, and final M4 report.

The current implementation provides a functional foundation for a student career companion while clearly identifying areas for future improvement in scalability, retrieval evaluation, LLM optimization, automated notifications, and production infrastructure.
