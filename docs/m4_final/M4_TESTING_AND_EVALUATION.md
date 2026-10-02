# M4.2 — Testing & Evaluation

## 1. Overview

Testing and evaluation for the AI Career Companion Agent were performed during Milestone 4 to verify that the major components work individually and as an integrated student workflow.

The testing strategy covers:

- API functionality
- End-to-end workflow execution
- RAG retrieval
- Job-resume matching
- Skill-gap analysis
- Resume customization
- Interview preparation
- Career Assistant
- Application tracking
- Error and edge-case handling
- Multi-agent consistency
- Performance measurement

The tests were executed against the local FastAPI application using the project's Python virtual environment.

---

## 2. Testing Objectives

The M4 testing phase was designed to verify that:

1. Core APIs return successful responses for valid inputs.
2. Resume upload and parsing work correctly.
3. Relevant internship/job records can be retrieved through the RAG pipeline.
4. Candidate-job matching produces structured results.
5. Skill gaps are identified from candidate and job information.
6. Resume customization remains grounded in candidate information.
7. Cover letters remain grounded in candidate information.
8. Interview preparation is generated from the selected job and candidate profile.
9. Career Assistant responses can use profile/job context.
10. Applications can be created, retrieved, updated, filtered, and deleted.
11. Invalid inputs are handled without crashing the application.
12. Multiple agents maintain consistent candidate/job information.
13. The complete workflow can execute successfully from profile creation through application tracking.
14. Response performance can be measured for the major workflow operations.

---

## 3. Testing Environment

The M4 tests were executed using the following environment:

| Component             | Version / Configuration |
| --------------------- | ----------------------- |
| Operating System      | Windows                 |
| Python                | 3.14.5                  |
| FastAPI               | 0.141.1                 |
| Starlette             | 1.6.0                   |
| HTTPX                 | 0.28.1                  |
| Google Gen AI SDK     | 2.23.0                  |
| AnyIO                 | 4.15.1                  |
| Pytest                | 9.1.1                   |
| Vector database/index | FAISS                   |
| Embedding model       | `all-MiniLM-L6-v2`      |
| Embedding dimension   | 384                     |
| Database              | SQLite                  |

The tests use the project's local virtual environment:

```text
.venv\Scripts\python.exe
```

---

# 4. M4 End-to-End Testing

## 4.1 Test Scope

The M4 E2E suite validates the complete career-companion workflow rather than testing individual APIs in isolation.

The workflow includes:

```text
Profile
   |
   v
Resume Upload
   |
   v
Resume Parsing
   |
   v
Internship Retrieval
   |
   v
Job-Resume Matching
   |
   v
Skill Gap Analysis
   |
   v
Resume Customization
   |
   v
Cover Letter
   |
   v
Interview Preparation
   |
   v
Career Assistant
   |
   v
Application Tracking
```

The test suite also includes error/edge-case testing and multi-agent consistency checks.

---

## 4.2 E2E Test Results

The completed M4 E2E test execution produced:

```text
Total Tests Executed : 80
PASS                 : 80
FAIL                 : 0
BLOCKED              : 0
```

Therefore, all 80 executed M4 E2E checks passed during the recorded test run.

Pytest also reported the test suite itself as successful:

```text
1 passed
```

The complete workflow execution took approximately:

```text
191.75 seconds
```

---

## 4.3 Functional Test Breakdown

The major test sections completed successfully.

| Test Area                 |     Result |
| ------------------------- | ---------: |
| Profile                   |   5/5 PASS |
| Resume                    |   4/4 PASS |
| RAG                       |   5/5 PASS |
| Matching                  |   4/4 PASS |
| Skill Gap                 |   5/5 PASS |
| Application Customization |   4/4 PASS |
| Interview                 |   5/5 PASS |
| Career Assistant          |   5/5 PASS |
| Application Tracker       | 16/16 PASS |
| Error / Edge Cases        |   9/9 PASS |
| Full E2E Workflow         |       PASS |
| Multi-Agent Consistency   |   4/4 PASS |

The exact number of checks in the combined workflow sections may vary by the internal test grouping, but the final recorded execution total was **80 tests with 80 passes**.

---

# 5. Profile Testing

Profile tests validate creation and retrieval of candidate information used throughout the career workflow.

The profile information includes fields such as:

- Full name
- Email
- Phone
- Location
- Target role
- LinkedIn URL

Successful profile creation establishes the candidate context required by downstream components.

The E2E test section achieved:

```text
Profile : 5/5 PASS
```

---

# 6. Resume Upload and Parsing Testing

Resume functionality was tested through the profile-to-resume workflow.

The system supports resume uploads in:

- PDF
- DOCX
- TXT

The test verifies that an uploaded resume can be associated with a candidate profile and processed into structured candidate information.

The extracted information can include:

- Summary
- Skills
- Education
- Experience
- Projects
- Certifications

The resume test section achieved:

```text
Resume : 4/4 PASS
```

### Grounding requirement

A key evaluation principle is that generated career outputs should be based on information actually available in the candidate profile and resume.

The system's agent prompts explicitly instruct the generation components not to invent unsupported:

- Skills
- Employers
- Projects
- Degrees
- Certifications
- Achievements
- Metrics
- Experience

---

# 7. RAG Testing

The RAG subsystem was evaluated as part of the E2E workflow.

The system uses:

- Curated internship/job records
- Section-based semantic chunks
- Sentence Transformer embeddings
- FAISS vector search
- Structured job reconstruction

The current knowledge base contains:

```text
102 jobs
388 semantic chunks/vectors
384-dimensional embeddings
```

The RAG test section achieved:

```text
RAG : 5/5 PASS
```

The test validates that the retrieval subsystem can return internship/job information for a candidate query.

---

# 8. Retrieval Relevance and Grounding

RAG evaluation considers whether retrieved information is relevant to the requested career context.

The architecture records the semantic similarity returned by FAISS for retrieved chunks.

Retrieved chunks are then deduplicated by `job_id` before the structured job records are loaded for downstream matching.

This reduces repeated processing of multiple chunks belonging to the same job posting.

The evaluation therefore distinguishes between:

```text
Semantic retrieval
        |
        v
Candidate job set
        |
        v
Structured matching
```

rather than treating raw vector similarity as the final job-match score.

---

# 9. Job-Resume Matching Testing

The Job-Resume Matching pipeline combines RAG retrieval with deterministic matching logic.

The matching process evaluates:

- Required skills
- Preferred skills
- Project relevance
- Education
- Experience
- Qualifications

The current deterministic scoring weights are:

| Component         | Weight |
| ----------------- | -----: |
| Required skills   |    40% |
| Preferred skills  |    15% |
| Project relevance |    15% |
| Education         |    10% |
| Experience        |    10% |
| Qualifications    |    10% |

The matching test section achieved:

```text
Matching : 4/4 PASS
```

The final match result includes:

- Match score
- Matched skills
- Missing skills
- Component scores
- Retrieval similarity
- Reasoning

---

# 10. Skill Gap Testing

Skill Gap analysis compares the candidate's available skills with the selected job's required and preferred skills.

The deterministic foundation calculates:

```text
Skill Match Percentage
```

from matched required and preferred skills.

The output distinguishes between:

- Strong matches
- Critical gaps
- Partial gaps
- Preferred gaps
- Experience gaps
- Qualification gaps
- Recommendations

When the LLM is unavailable, the system provides a deterministic fallback instead of failing the request.

The test section achieved:

```text
Skill Gap : 5/5 PASS
```

---

# 11. Application Customization Testing

The Application Agent supports:

- Tailored resume generation
- Cover-letter generation

The customization process receives both candidate and job information.

The generated resume can contain:

- Professional summary
- Highlighted skills
- Projects
- Experience
- Education
- Certifications
- Suggested keywords
- Customization strategy

The cover-letter process generates structured sections including:

- Opening
- Skills alignment
- Project alignment
- Company fit
- Closing
- Sign-off
- Full letter

The test section achieved:

```text
Application Customization : 4/4 PASS
```

---

# 12. Interview Preparation Testing

The Interview Agent generates interview preparation based on candidate and selected-job information.

The supported question categories include:

- Technical
- Resume
- Project
- Role-specific
- HR

Preparation output includes question-specific guidance and answer frameworks.

The Interview test section achieved:

```text
Interview : 5/5 PASS
```

The system also supports mock-interview answer evaluation.

---

# 13. Career Assistant Testing

The Career Assistant provides profile-aware conversational career guidance.

The assistant can use:

- Candidate name
- Target role
- Skills
- Projects
- Education
- Selected job
- Required skills
- Preferred skills
- Skill-gap information
- Conversation history

The system supports multi-turn context by including recent conversation history in the LLM request.

The test section achieved:

```text
Career Assistant : 5/5 PASS
```

---

# 14. Application Tracker Testing

Application Tracking was extensively tested as part of M4.

The tracker supports:

- Application creation
- Application retrieval
- Application update
- Application deletion
- Status validation
- Duplicate detection
- Company filtering
- Role filtering
- Status filtering
- Application-date filtering
- General search
- Deadline filtering
- Dashboard metrics

The application tracker section achieved:

```text
Application Tracker : 16/16 PASS
```

This validates the tracker as an integrated component of the student workflow.

---

# 15. Error and Edge-Case Testing

The M4 test suite includes dedicated error and edge-case scenarios.

The recorded result was:

```text
Error / Edge Cases : 9/9 PASS
```

These tests verify that invalid or incomplete requests are handled through appropriate API responses rather than causing uncontrolled application failures.

Examples include validation of:

- Invalid resource identifiers
- Invalid application statuses
- Missing/invalid inputs
- Duplicate application creation
- Application/profile relationships

---

# 16. Multi-Agent Consistency Testing

The project contains multiple specialized agents/components.

The M4 evaluation checks whether outputs remain consistent with shared candidate and job information.

The multi-agent consistency section achieved:

```text
4/4 PASS
```

The consistency requirement focuses on avoiding contradictions and unsupported information between:

- Skill Gap Agent
- Application Agent
- Interview Agent
- Career Assistant

The agents receive grounded candidate/job context rather than independently inventing candidate information.

---

# 17. LLM Failure and Fallback Testing

The system includes deterministic fallback behavior for several AI-assisted operations.

During the recorded M4.3 performance run, the Gemini API quota for the configured model had been exhausted.

As a result, some LLM operations logged quota-related failures and used local/deterministic fallback behavior.

Importantly, the API operations still completed successfully.

This demonstrates that the current architecture does not make every application operation completely dependent on successful LLM generation.

The fallback mechanism is particularly relevant for:

- Resume parsing
- Matching explanation
- Skill-gap analysis
- Resume customization
- Cover-letter generation
- Interview preparation
- Career Assistant responses

The fallback outputs should be considered deterministic backup behavior rather than equivalent to a successful LLM response.

---

# 18. Performance Testing

Performance was measured separately through:

```text
backend/test_m43_performance.py
```

The test executed the major workflow operations sequentially.

Recorded results:

| Operation             |       Time |
| --------------------- | ---------: |
| Health                |    0.010 s |
| Resume upload         | Successful |
| RAG job search        |    0.068 s |
| Job matching          |    2.435 s |
| Skill gap             |   24.980 s |
| Resume customization  |   24.017 s |
| Cover letter          |   25.674 s |
| Interview preparation |   24.502 s |
| Career Assistant      |   23.224 s |

The complete recorded performance run reported:

```text
Successful operations : 9
Failed operations     : 0
Total time            : 124.909 s
Average               : 15.614 s
Median                : 23.621 s
Fastest               : 0.010 s
Slowest               : 25.674 s
```

The test concluded with:

```text
M4.3 PERFORMANCE TEST PASSED
```

Pytest reported:

```text
1 passed
```

with the complete performance test execution taking approximately:

```text
171.58 seconds
```

---

# 19. Performance Interpretation

The measurements show a clear difference between lightweight local operations and generation-heavy operations.

### Low-latency operations

Health checking and RAG retrieval are relatively fast:

```text
Health      : 0.010 s
RAG search  : 0.068 s
```

### Matching

Job matching took:

```text
2.435 s
```

This includes retrieval-related processing and deterministic matching over candidate jobs.

### Generation-heavy operations

Skill-gap analysis, resume customization, cover-letter generation, interview preparation, and Career Assistant requests were approximately 23–26 seconds in the recorded run.

These operations can be affected by:

- LLM request latency
- LLM availability
- Prompt size
- Candidate/job context size
- Fallback processing
- Network/API conditions

Therefore, the performance numbers represent the recorded local test environment rather than a universal production latency guarantee.

---

# 20. Performance Test Success Criteria

The performance test was designed to count an operation as successful only when the API returned an HTTP status in the successful 2xx range.

This is important because an HTTP 404 or 405 response should not be interpreted as a successful performance measurement.

The test therefore distinguishes:

```text
HTTP success
```

from:

```text
HTTP failure
```

and records the response time only as part of the operation measurement.

---

# 21. Test Reliability and Repeatability

The E2E workflow was adjusted to use a unique profile email for each full workflow execution.

This prevents persisted test data from causing false failures due to duplicate records between repeated test runs.

At the same time, the application's real duplicate-application protection remains enabled and is explicitly tested.

This provides two separate behaviors:

```text
E2E test isolation
        +
Production duplicate protection
```

---

# 22. Known Warnings

The successful M4 test execution produced several deprecation and environment warnings.

Observed categories included:

- Starlette/httpx TestClient deprecation warning
- AnyIO `BlockingPortal` deprecation warning
- FastAPI `on_event` startup deprecation warning
- `datetime.utcnow()` deprecation warnings in the E2E test
- Google Gen AI type-related deprecation warning
- Hugging Face Hub unauthenticated-access warning
- Gemini quota-related warnings

These warnings did not cause the recorded M4 functional tests to fail.

They represent technical-debt or environment-maintenance items for future cleanup rather than current functional test failures.

---

# 23. Evaluation Summary

The M4 testing phase produced the following recorded outcomes:

| Evaluation Area           | Result         |
| ------------------------- | -------------- |
| Functional E2E tests      | 80/80 PASS     |
| Profile tests             | 5/5 PASS       |
| Resume tests              | 4/4 PASS       |
| RAG tests                 | 5/5 PASS       |
| Matching tests            | 4/4 PASS       |
| Skill Gap tests           | 5/5 PASS       |
| Application Customization | 4/4 PASS       |
| Interview tests           | 5/5 PASS       |
| Career Assistant          | 5/5 PASS       |
| Application Tracker       | 16/16 PASS     |
| Error/Edge tests          | 9/9 PASS       |
| Multi-Agent Consistency   | 4/4 PASS       |
| Performance operations    | 9/9 successful |
| Performance test          | PASS           |

---

# 24. Testing Limitations

The current evaluation has several limitations.

### Dataset size

The current internship knowledge base contains 102 curated jobs. A larger production-scale dataset would be required to evaluate retrieval scalability more comprehensively.

### Manual evaluation

The M2 evaluation used manually selected sample profiles and evaluated retrieved results. A larger manually labeled relevance dataset would provide stronger quantitative retrieval evaluation.

### LLM dependency

Generation latency and output quality can vary depending on external LLM availability, quotas, network conditions, and model behavior.

### Fallback evaluation

Deterministic fallback responses provide resilience but are not equivalent to LLM-generated responses and should be evaluated separately for quality.

### Performance environment

The recorded performance measurements were obtained from a local development environment and should not be interpreted as production-scale benchmarks.

### Warning cleanup

Several dependency deprecation warnings remain and can be addressed during future maintenance.

---

# 25. Future Evaluation Improvements

Future testing can extend the evaluation framework with:

- Larger labeled retrieval datasets.
- Precision@K and Recall@K measurements.
- Mean Reciprocal Rank (MRR).
- Retrieval relevance annotation.
- Automated hallucination/grounding checks.
- Larger candidate-profile test sets.
- Load testing with concurrent users.
- LLM token-usage measurements.
- Memory/resource monitoring.
- Database performance benchmarks.
- Production deployment benchmarks.
- Automated regression testing in CI/CD.

---

# 26. Conclusion

The M4 testing phase validates the core integrated workflow of the AI Career Companion Agent.

The recorded E2E execution achieved:

```text
80 tests
80 passed
0 failed
0 blocked
```

Application Tracking achieved **16/16 PASS**, while the major functional sections also completed successfully.

The separate M4.3 performance test recorded **9 successful operations with 0 failures** and completed with the status:

```text
M4.3 PERFORMANCE TEST PASSED
```

The results demonstrate that the implemented components can operate together as an integrated career-assistance workflow in the tested local environment.

The evaluation also identifies clear areas for future improvement, particularly larger-scale retrieval evaluation, production-scale performance testing, LLM quality measurement, and dependency-warning cleanup.
