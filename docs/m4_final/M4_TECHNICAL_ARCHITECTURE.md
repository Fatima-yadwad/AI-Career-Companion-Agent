# AI Career Companion Agent

## Milestone 4.4 – Technical Architecture

**Project:** AI Career Companion Agent
**Milestone:** M4.4 – Documentation and Final Integration
**Architecture Version:** 0.6.0

---

## 1. Introduction

The AI Career Companion Agent is a student-focused career assistance system designed to support the complete internship/job application workflow.

The system combines:

- Resume processing and structured candidate profiling
- Retrieval-Augmented Generation (RAG)
- Semantic job retrieval
- Deterministic job-resume matching
- Skill gap analysis
- Resume customization
- Cover letter generation
- Interview preparation
- Mock interview evaluation
- Context-aware career assistance
- Application tracking and management
- Authentication and profile management

The backend is implemented using FastAPI and uses SQLite for persistent application data. A FAISS vector index and Sentence Transformer embeddings provide semantic retrieval over a curated internship/job knowledge base.

The architecture follows a **grounded multi-agent service design**. Agent modules use structured candidate and job information as input and can use an LLM for natural-language generation. Deterministic fallback logic is provided for important capabilities when the LLM is unavailable or rate-limited.

---

# 2. High-Level System Architecture

```text
                         STUDENT / USER
                               |
                               v
                    +-----------------------+
                    |     FastAPI Backend   |
                    |      backend/main.py  |
                    +-----------+-----------+
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
 +-------------+        +---------------+       +---------------+
 | User/Profile|        | Resume        |       | Job Search    |
 | Management  |        | Processing    |       | and Matching  |
 +------+------+        +-------+-------+       +-------+-------+
        |                       |                       |
        v                       v                       v
 +-------------+        +---------------+       +---------------+
 | SQLite      |        | Text/PDF/DOCX |       | RAG Pipeline  |
 | Database    |        | Extraction     |       | FAISS         |
 +-------------+        +-------+-------+       +-------+-------+
                                |                       |
                                v                       v
                       Structured Candidate      Retrieved Jobs
                                |                       |
                                +-----------+-----------+
                                            |
                                            v
                                  +--------------------+
                                  | Matching Service   |
                                  +---------+----------+
                                            |
                         +------------------+------------------+
                         |                  |                  |
                         v                  v                  v
                   Skill Gap Agent   Application Agent   Interview Agent
                         |                  |                  |
                         v                  v                  v
                   Skill Analysis    Resume/Cover Letter   Interview Prep
                         |                  |                  |
                         +------------------+------------------+
                                            |
                                            v
                                  Career Assistant
                                            |
                                            v
                                  Application Tracker
                                            |
                                            v
                                      SQLite DB
```

---

# 3. Backend Technology Stack

| Layer                  | Technology                          |
| ---------------------- | ----------------------------------- |
| Programming Language   | Python                              |
| API Framework          | FastAPI                             |
| Database               | SQLite                              |
| API Validation         | Pydantic                            |
| Authentication         | JWT + bcrypt                        |
| Semantic Embeddings    | Sentence Transformers               |
| Embedding Model        | `all-MiniLM-L6-v2`                  |
| Vector Search          | FAISS                               |
| LLM Integration        | Google Gemini through `llm_service` |
| Resume PDF Extraction  | pypdf                               |
| Resume DOCX Extraction | python-docx                         |
| Testing                | pytest                              |
| Job Knowledge Base     | JSON                                |
| Vector Metadata        | JSON                                |

---

# 4. FastAPI Application Layer

The main application is implemented in:

`backend/main.py`

FastAPI acts as the central orchestration layer between the frontend/client and backend services.

The API provides functionality for:

- Health checking
- Profile creation and management
- Authentication
- Resume upload and parsing
- Job search
- Job-resume matching
- Skill gap analysis
- Resume customization
- Cover letter generation
- Interview preparation
- Mock interviews
- Career assistant conversations
- Application tracking
- Application dashboard and filtering

The API also coordinates the RAG retriever, matching service, agent modules and database operations.

---

# 5. Data and Persistence Layer

The application uses SQLite:

`backend/data/career_companion.db`

The database contains tables for the major student workflow components.

Main tables include:

- `users`
- `profiles`
- `resumes`
- `skill_gaps`
- `customized_resumes`
- `cover_letters`
- `interview_preps`
- `mock_interviews`
- `mock_interview_answers`
- `chat_messages`
- `auth_sessions`
- `applications`

Indexes are used for frequently queried information such as:

- User email
- Profile/user relationship
- Application/profile relationship
- Application status
- Chat profile/conversation/time

This provides persistent storage across API requests.

---

# 6. Authentication Architecture

The application includes authentication using:

- bcrypt password hashing
- JWT access tokens
- HS256 signing
- Token expiration
- Session/JTI storage in `auth_sessions`

Authentication is used to associate users with their profiles and application information.

Profile access checks ensure that authenticated users can access and modify their own profile-related information.

---

# 7. Resume Processing Pipeline

The resume workflow begins with:

`POST /profiles/{profile_id}/resumes`

Supported formats:

- TXT
- PDF
- DOCX

The uploaded resume is stored under:

`backend/data/uploads`

Text extraction is performed according to file type:

```text
Resume Upload
      |
      +--> TXT  --> Direct text extraction
      |
      +--> PDF  --> pypdf extraction
      |
      +--> DOCX --> python-docx extraction
      |
      v
Extracted Resume Text
      |
      v
Structured Candidate Information
```

The structured candidate representation may contain:

- Summary
- Skills
- Education
- Experience
- Projects
- Certifications

Gemini can be used for structured extraction. A local deterministic extraction fallback is available when the LLM is unavailable.

The extraction prompt explicitly requires the system not to invent candidate information.

---

# 8. RAG Knowledge Base

The internship/job knowledge base is stored in:

`data/processed/internship_jobs.json`

The current curated knowledge base documented during M2 contains:

- 102 job records
- 388 semantic chunks/vectors
- 384-dimensional embeddings

The dataset is loaded using:

`backend/rag/loader.py`

The loader validates that the dataset exists and that its root structure is a JSON list.

---

# 9. RAG Chunking Strategy

Semantic chunks are generated using:

`backend/rag/chunker.py`

Each job can produce separate chunks for the following sections:

1. Job description
2. Responsibilities
3. Required skills
4. Preferred skills
5. Qualifications
6. Experience requirements
7. Education requirements

Each chunk retains identifying metadata:

- Job ID
- Job title
- Company
- Location
- Section
- Chunk text

This allows a retrieved semantic chunk to be mapped back to the complete structured job record.

---

# 10. Embedding Model

The RAG system uses:

`all-MiniLM-L6-v2`

through the Sentence Transformers library.

The implementation generates normalized embeddings.

The resulting embedding dimension is:

**384**

Normalization allows inner-product similarity to behave as cosine similarity for the retrieval process.

The embedding implementation is located in:

`backend/rag/embeddings.py`

---

# 11. FAISS Vector Store

The vector store is implemented in:

`backend/rag/vector_store.py`

The system uses:

`faiss.IndexFlatIP`

where IP represents Inner Product.

Because the embeddings are normalized, inner-product similarity corresponds to cosine similarity.

The generated vector store contains:

```text
backend/data/vector_store/
    |
    +-- jobs.index
    |
    +-- metadata.json
```

The index and metadata are validated when the `JobRetriever` starts.

The system checks that:

```text
FAISS vector count == metadata record count
```

If they do not match, initialization fails rather than silently returning inconsistent retrieval results.

---

# 12. Runtime RAG Retrieval

The retriever is implemented in:

`backend/rag/retriever.py`

At runtime:

```text
Natural Language Query
        |
        v
all-MiniLM-L6-v2
        |
        v
384-dimensional normalized vector
        |
        v
FAISS IndexFlatIP
        |
        v
Top-K semantic results
```

The retriever returns:

- Job ID
- Job title
- Company
- Location
- Section
- Retrieved text
- Similarity score

The retrieved similarity value is retained for downstream matching and evaluation.

---

# 13. Job-Resume Matching Architecture

The matching layer consists of:

- `backend/matching/matcher.py`
- `backend/matching/service.py`
- `backend/matching/job_loader.py`

The `MatchingService` first constructs a semantic candidate query using available candidate information:

- Candidate summary
- Skills
- Target role

The RAG retriever initially retrieves more candidates than the final requested result count:

```text
retrieval_count = top_k × 3
```

with bounds of 5 to 20 results.

This provides a larger semantic candidate pool before deterministic scoring.

---

# 14. Retrieval Deduplication

Multiple semantic chunks may belong to the same job.

The matching service therefore deduplicates retrieved results using:

`job_id`

The unique job IDs are then used to retrieve the complete structured records from:

`internship_jobs.json`

This separates:

**semantic retrieval**

from:

**complete job-level matching**

and prevents multiple chunks from the same job from occupying the final recommendation list.

---

# 15. Deterministic Matching Engine

The matching engine is implemented in:

`backend/matching/matcher.py`

It evaluates multiple dimensions.

### Matching dimensions

- Required skills
- Preferred skills
- Project relevance
- Education
- Experience
- Qualifications

Skill aliases are normalized before comparison.

Examples include:

| Input    | Normalized form             |
| -------- | --------------------------- |
| ML       | machine learning            |
| DL       | deep learning               |
| AI       | artificial intelligence     |
| CV       | computer vision             |
| NLP      | natural language processing |
| JS       | javascript                  |
| TS       | typescript                  |
| sklearn  | scikit-learn                |
| postgres | postgresql                  |

This reduces mismatches caused by common naming variations.

---

# 16. Job Match Score

The current deterministic score uses the following weighted formula:

```text
Match Score =
    40% × Required Skill Score
  + 15% × Preferred Skill Score
  + 15% × Project Score
  + 10% × Education Score
  + 10% × Experience Score
  + 10% × Qualification Score
```

Total:

**100%**

The final score is capped at 100 and rounded to two decimal places.

Retrieval similarity is recorded separately and is not directly included as a weighted component of this formula.

---

# 17. Matching Output

Each match result contains information such as:

- Job ID
- Job title
- Company
- Location
- Work type
- Match score
- Matched skills
- Missing required skills
- Required skill score
- Preferred skill score
- Project score
- Education score
- Experience score
- Qualification score
- Retrieval similarity
- Human-readable reasoning

Results are sorted by `match_score` in descending order and limited to the requested top-K results.

---

# 18. Multi-Agent Service Architecture

The project implements multiple specialized agent modules.

The main agent modules are:

```text
backend/agents/
    |
    +-- skill_gap_agent.py
    +-- application_agent.py
    +-- interview_agent.py
    +-- career_assistant.py
```

These modules are orchestrated by the FastAPI application.

The system uses a specialized-agent approach where each module has a focused responsibility.

---

# 19. Skill Gap Agent

File:

`backend/agents/skill_gap_agent.py`

The Skill Gap Agent compares the candidate's verified skills with the selected job.

It separates:

- Matched required skills
- Missing required skills
- Matched preferred skills
- Missing preferred skills

It can additionally generate:

- Strong matches
- Critical gaps
- Partial gaps
- Preferred gaps
- Experience gaps
- Qualification gaps
- Actionable recommendations

The deterministic skill analysis is performed before LLM generation.

The agent calculates the skill match percentage from required and preferred skill sets.

---

# 20. Application Agent

File:

`backend/agents/application_agent.py`

The Application Agent provides two major functions:

### Resume Customization

The customized resume can contain:

- Professional summary
- Highlighted skills
- Projects
- Experience
- Education
- Certifications
- Suggested keywords
- Customization strategy

### Cover Letter Generation

The cover letter generation includes:

- Subject line
- Salutation
- Opening paragraph
- Skills alignment
- Project experience
- Company fit
- Closing
- Sign-off
- Complete letter

The agent is explicitly instructed not to invent:

- Employers
- Projects
- Degrees
- Certifications
- Skills
- Metrics
- Achievements

---

# 21. Interview Agent

File:

`backend/agents/interview_agent.py`

The Interview Agent provides:

- Technical questions
- Resume questions
- Project questions
- Role-specific questions
- HR/behavioral questions

Each question can include:

- Preparation guide
- Suggested topics
- Answer framework

The agent also supports mock interview answer evaluation.

Mock answers are evaluated across:

1. Technical understanding
2. Relevance
3. Clarity
4. Completeness
5. Project understanding

The system also provides:

- Overall score
- Strengths
- Areas for improvement
- Suggested answer structure

---

# 22. Career Assistant

File:

`backend/agents/career_assistant.py`

The Career Assistant provides context-aware conversational career guidance.

The context may include:

- Candidate name
- Target role
- Skills
- Projects
- Education
- Selected job
- Required skills
- Preferred skills
- Skill gap information
- Recent conversation history

The implementation includes the latest six conversation turns when constructing the LLM dialogue context.

The API persists conversation messages in the `chat_messages` database table.

This enables profile-aware and job-specific career conversations.

---

# 23. LLM Integration and Grounding

The agents use the shared:

`backend/services/llm_service.py`

for structured LLM generation.

The LLM is used primarily for:

- Natural-language generation
- Structured career guidance
- Resume tailoring
- Cover letters
- Skill-gap recommendations
- Interview preparation
- Mock interview evaluation
- Career assistant responses

The system follows a grounded-generation approach.

Prompts provide structured candidate and job evidence to the LLM.

The agents explicitly instruct the model not to invent unsupported candidate facts.

---

# 24. Deterministic Fallback Architecture

A major reliability feature is the presence of deterministic fallback logic.

The following capabilities have fallback implementations:

- Resume extraction
- Job matching explanations
- Skill gap analysis
- Resume customization
- Cover letter generation
- Interview preparation
- Mock answer evaluation
- Career assistant responses

The general pattern is:

```text
Structured Input
      |
      v
Deterministic Foundation
      |
      v
LLM Generation
      |
   success?
    /   \
  yes    no
  |       |
  v       v
LLM      Deterministic
Result    Fallback
```

This allows the API to remain operational even when the LLM service is unavailable or rate-limited.

---

# 25. Application Tracking Architecture

Application tracking is integrated into the same FastAPI backend.

The application tracker stores:

- Company
- Job title
- Job description
- Application date
- Deadline
- Status
- Interview date
- Interview status
- Notes
- Follow-up information
- Generated resume
- Generated cover letter

Supported application statuses include:

- Saved
- Planning to apply
- Applied
- Application under review
- Shortlisted
- Interview scheduled
- Interview completed
- Offer received
- Rejected
- Withdrawn

Duplicate applications for the same profile and job are prevented.

---

# 26. Application Search and Filtering

The tracker supports filtering and searching by:

- Company
- Role
- Status
- Deadline
- Application date
- Free-text search

Deadline filters include:

- Upcoming
- Overdue
- Has deadline

The application dashboard also provides metrics and lists for:

- Total applications
- Active applications
- Upcoming deadlines
- Scheduled interviews
- Offers
- Rejected applications
- Recent applications
- Upcoming interviews
- Applications requiring follow-up

---

# 27. Complete Student Workflow

The intended end-to-end workflow is:

```text
1. Create Account/Profile
          |
          v
2. Upload Resume
          |
          v
3. Extract Structured Candidate Profile
          |
          v
4. Search Internship/Job Knowledge Base
          |
          v
5. Retrieve Semantically Relevant Jobs
          |
          v
6. Calculate Job-Resume Match
          |
          v
7. Select Target Job
          |
          v
8. Analyze Skill Gaps
          |
          v
9. Customize Resume
          |
          v
10. Generate Cover Letter
          |
          v
11. Generate Interview Preparation
          |
          v
12. Practice Mock Interview
          |
          v
13. Receive Answer Evaluation
          |
          v
14. Track Application
          |
          v
15. Continue Career Assistant Conversation
```

This workflow integrates the major M3 capabilities with the M4 application management layer.

---

# 28. Data Flow Between Major Components

The main information flow is:

```text
Resume
  |
  v
Candidate Profile
  |
  +------------------+
  |                  |
  v                  v
RAG Query        Agent Context
  |                  |
  v                  |
Job Retrieval        |
  |                  |
  v                  |
Matching Service <---+
  |
  v
Selected Job
  |
  +----------+-----------+-------------+
  |          |           |             |
  v          v           v             v
Skill Gap  Resume     Interview    Career
Analysis   /Letter     Preparation  Assistant
  |          |           |             |
  +----------+-----------+-------------+
             |
             v
      Application Tracker
             |
             v
          SQLite
```

---

# 29. Error Handling and Reliability

The backend includes validation and fallback mechanisms for common failure conditions.

Examples include:

- Missing profile
- Missing uploaded resume
- Missing or invalid job
- Missing required application fields
- Duplicate applications
- Empty retrieval queries
- Missing RAG index
- Missing RAG metadata
- FAISS/metadata size mismatch
- LLM failures
- LLM rate limiting

The system attempts to return structured API responses rather than allowing downstream failures to silently produce invalid results.

---

# 30. Performance Considerations

The architecture separates retrieval and deterministic scoring to avoid performing expensive generation for every job.

The matching flow first narrows the search space using semantic retrieval.

The current retrieval strategy uses a bounded expanded candidate pool:

```text
Requested top-K
      |
      v
Retrieve up to top-K × 3
      |
      v
Deduplicate jobs
      |
      v
Deterministic scoring
      |
      v
Return top-K
```

The embedding model is loaded once by the retriever rather than recreated for every query.

The FAISS index also provides efficient vector similarity search over the stored job embeddings.

---

# 31. Security and Data Isolation

Authentication and profile ownership checks are used to protect profile-related data.

Important mechanisms include:

- Password hashing using bcrypt
- JWT-based authentication
- Session/JTI tracking
- Token expiration
- Profile ownership validation
- User-specific application records
- User-specific conversation history

Sensitive configuration such as API credentials is loaded from environment configuration rather than being hard-coded into the application logic.

---

# 32. Testing Architecture

The project includes API and integration testing using pytest.

The M4 testing strategy covers:

- Profile operations
- Resume upload
- Resume parsing
- RAG job retrieval
- Job-resume matching
- Skill gap analysis
- Resume customization
- Cover letter generation
- Interview preparation
- Career assistant
- Application tracker
- Error and edge cases
- Full end-to-end workflow
- Multi-agent consistency
- Performance measurements

The end-to-end workflow validates the integration of the major student journey components.

---

# 33. M4.3 Performance Validation

The M4.3 performance test validated the main API workflow.

The recorded test run produced successful HTTP 2xx responses for:

- Health check
- Resume upload
- RAG job search
- Job matching
- Skill gap analysis
- Resume customization
- Cover letter generation
- Interview preparation
- Career assistant

The measured run contained:

- **9 successful operations**
- **0 failed operations**
- **Total measured time: approximately 124.9 seconds**
- **Average operation time: approximately 15.6 seconds**
- **Fastest operation: approximately 0.01 seconds**
- **Slowest operation: approximately 25.7 seconds**

The performance test completed successfully.

LLM quota limitations were handled through the application's fallback mechanisms rather than causing the API workflow to fail.

---

# 34. M4 End-to-End Validation

The M4 end-to-end test suite validated the complete workflow.

The successful test run reported:

```text
Total Tests Executed : 80
PASS                 : 80
FAIL                 : 0
BLOCKED              : 0
```

The tested sections included:

- Profile
- Resume
- RAG
- Matching
- Skill Gap
- Application Customization
- Interview
- Career Assistant
- Application Tracker
- Error/Edge Cases
- Full E2E Workflow
- Multi-Agent Consistency

This demonstrates successful integration of the major backend components under the tested conditions.

---

# 35. Architecture Design Principles

The implementation follows several important design principles.

### 35.1 Grounded generation

LLM prompts receive structured candidate and job information and explicitly prohibit unsupported candidate claims.

### 35.2 Deterministic core logic

Important matching calculations are performed deterministically rather than delegated entirely to the LLM.

### 35.3 Modular agents

Career functions are separated into specialized agent modules.

### 35.4 Retrieval before generation

The RAG system identifies relevant jobs before downstream matching and generation.

### 35.5 Structured outputs

The agents request structured JSON responses for predictable API integration.

### 35.6 Graceful degradation

Deterministic fallbacks allow important capabilities to continue functioning when LLM generation fails.

### 35.7 Persistent workflow

SQLite stores generated artifacts, applications, conversations and other workflow information.

---

# 36. Current Architectural Limitations

The current implementation has several limitations that should be considered during future development.

1. The internship/job knowledge base is relatively small.
2. RAG retrieval quality depends on the quality and coverage of the curated job dataset.
3. The deterministic experience matching logic is currently simplified.
4. Qualification matching uses keyword-based comparison.
5. Project relevance currently relies on normalized text and skill overlap.
6. Retrieval similarity is recorded but is not currently part of the final weighted match score.
7. LLM-generated capabilities depend on model availability and quota.
8. Some fallback outputs are less detailed than LLM-generated responses.
9. The current architecture is implemented as specialized Python service/agent modules rather than a dedicated external multi-agent orchestration framework.

These limitations provide opportunities for future optimization and evaluation.

---

# 37. Future Technical Improvements

Potential improvements include:

- Larger and continuously updated internship/job knowledge base
- Improved semantic chunking
- Evaluation of alternative embedding models
- Hybrid lexical + semantic retrieval
- Retrieval reranking
- More sophisticated experience-level matching
- Improved qualification parsing
- Better location and work-type compatibility
- Explicit required-skill importance weighting
- Retrieval-quality evaluation using manually labeled relevance data
- LLM response quality evaluation
- Token and latency monitoring
- Caching of repeated LLM requests
- Asynchronous processing for expensive operations
- Improved application reminder scheduling
- More advanced conversation memory
- Dedicated agent orchestration if future requirements justify it

---

# 38. Conclusion

The AI Career Companion Agent combines a semantic RAG pipeline, deterministic job matching engine, specialized career agents, persistent application tracking and authenticated user management into a single student career workflow.

The architecture separates:

- **Retrieval** for finding relevant opportunities
- **Deterministic matching** for measurable candidate-job alignment
- **LLM agents** for natural-language career assistance and content generation
- **Fallback logic** for reliability
- **SQLite persistence** for long-running application workflows

The resulting architecture supports the complete workflow from resume upload and job discovery through skill-gap analysis, application preparation, interview practice and application tracking.
