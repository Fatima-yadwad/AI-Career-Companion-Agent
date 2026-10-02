# M4.3 — Optimization & Performance

## 1. Overview

Milestone 4.3 focuses on optimization and performance evaluation of the AI Career Companion Agent.

The optimization work covers the major processing layers of the system:

- RAG retrieval
- Semantic embeddings
- FAISS vector search
- Job-level deduplication
- Job-resume matching
- Skill matching
- Application generation
- Interview preparation
- Career Assistant
- LLM prompt design
- Deterministic fallback processing
- API response performance

The objective is to understand the current performance characteristics of the system, identify bottlenecks, and define practical improvements for future production scaling.

---

# 2. Optimization Objectives

The M4.3 optimization work addresses the following objectives:

1. Reduce unnecessary RAG retrieval work.
2. Keep the vector-search pipeline lightweight.
3. Avoid duplicate processing of chunks belonging to the same job.
4. Limit the number of candidate jobs passed to the matching layer.
5. Use deterministic scoring where an LLM is not required.
6. Keep agent prompts grounded in available candidate/job information.
7. Provide fallback behavior when LLM generation is unavailable.
8. Measure response time for the major workflow operations.
9. Identify the dominant latency sources.
10. Define future improvements for larger datasets and concurrent users.

---

# 3. RAG Optimization

## 3.1 Section-Based Chunking

The job knowledge base is divided into semantic sections rather than treating an entire job posting as one vector.

The current chunking implementation can create separate chunks for:

- Job description
- Responsibilities
- Required skills
- Preferred skills
- Qualifications
- Experience requirements
- Education requirements

Each chunk retains metadata such as:

- Job ID
- Job title
- Company
- Location
- Section
- Text

This provides more targeted retrieval because a query can match the relevant part of a job posting.

---

# 4. Embedding Model

The RAG pipeline uses:

```text id="u5o7zi"
all-MiniLM-L6-v2
```

from Sentence Transformers.

The generated embeddings are normalized before being stored and searched.

The current embedding dimension is:

```text id="1v5g8c"
384
```

Normalized embeddings allow the FAISS inner-product index to represent cosine similarity.

This provides a lightweight semantic retrieval mechanism suitable for the current internship knowledge base.

---

# 5. FAISS Vector Index

The vector store uses:

```text id="w2x0l3"
FAISS IndexFlatIP
```

where `IP` represents inner product.

The current vector store contains:

```text id="r0c4sx"
102 jobs
388 semantic chunks
388 vectors
384 dimensions
```

The vector index is loaded at runtime rather than rebuilding embeddings for every API request.

This avoids repeatedly performing the expensive embedding-generation and index-building steps during normal retrieval.

---

# 6. Vector Store Integrity

The RAG retriever validates the vector store during initialization.

It loads:

```text id="2d8k2f"
jobs.index
metadata.json
```

and verifies that:

```text id="n7z3eh"
index.ntotal == len(metadata)
```

If the number of FAISS vectors and metadata records does not match, initialization fails instead of silently returning incorrectly mapped results.

This integrity check reduces the risk of vector-to-job metadata mismatches.

---

# 7. Retrieval Parameter Optimization

The matching service does not retrieve only the final requested number of jobs.

For a requested `top_k`, it retrieves a larger bounded candidate set:

```text id="2qk5x0"
retrieval_top_k = min(max(top_k * 3, 5), 20)
```

The purpose is to provide the deterministic matching layer with additional candidate jobs.

For example, a request for five final matches can retrieve up to 15 candidate results before downstream processing.

The value is also bounded at 20 to prevent unnecessarily large candidate sets.

---

# 8. Job-Level Deduplication

Because multiple semantic chunks can belong to the same job posting, raw vector retrieval may contain repeated job IDs.

The matching service therefore deduplicates retrieved chunks by `job_id`.

The processing pipeline becomes:

```text id="1v1j6a"
Query
  |
  v
FAISS semantic retrieval
  |
  v
Retrieved chunks
  |
  v
Deduplicate by job_id
  |
  v
Load structured job records
  |
  v
Deterministic matching
  |
  v
Sort by match score
  |
  v
Final top-k jobs
```

This prevents multiple chunks from the same job from unnecessarily occupying the downstream candidate set.

---

# 9. Structured Job Reconstruction

After retrieval, the matching service loads complete structured job records using their `job_id`.

This is important because a single semantic chunk does not necessarily contain every attribute required by the matching algorithm.

The structured job record supplies information such as:

- Required skills
- Preferred skills
- Description
- Responsibilities
- Qualifications
- Education requirements
- Experience requirements

The system therefore uses semantic retrieval for candidate discovery and structured data for detailed scoring.

---

# 10. Matching Optimization

The Job-Resume Matching system uses a deterministic scoring layer after RAG retrieval.

The current scoring components are:

| Component         |   Weight |
| ----------------- | -------: |
| Required skills   |      40% |
| Preferred skills  |      15% |
| Project relevance |      15% |
| Education         |      10% |
| Experience        |      10% |
| Qualifications    |      10% |
| **Total**         | **100%** |

This approach avoids requiring an LLM to calculate the core numerical match score.

The result is reproducible for the same candidate and job inputs.

---

# 11. Required vs Preferred Skills

The matching implementation treats required and preferred skills separately.

Required skills have the highest weighting:

```text id="1u8o4x"
40%
```

Preferred skills contribute:

```text id="4g2p8d"
15%
```

The output also separates:

- `matched_skills`
- `missing_skills`

where missing skills primarily represent missing required skills.

This provides a more interpretable score than using semantic similarity alone.

---

# 12. Skill Normalization

The matching module normalizes skills before comparison.

Examples of supported aliases include:

| Input              | Normalized form               |
| ------------------ | ----------------------------- |
| `ml`               | `machine learning`            |
| `machine-learning` | `machine learning`            |
| `dl`               | `deep learning`               |
| `ai`               | `artificial intelligence`     |
| `cv`               | `computer vision`             |
| `nlp`              | `natural language processing` |
| `js`               | `javascript`                  |
| `ts`               | `typescript`                  |
| `postgres`         | `postgresql`                  |
| `sklearn`          | `scikit-learn`                |

This reduces false mismatches caused by common naming variations.

---

# 13. Project Relevance

Project relevance contributes 15% to the final matching score.

The implementation builds project text from candidate project information, including available:

- Project names
- Project descriptions
- Technologies

It then compares candidate skills with job-related text containing:

- Job description
- Responsibilities
- Required skills
- Preferred skills

This allows project-related technical skills to contribute to job compatibility.

---

# 14. Education and Experience Components

Education contributes 10% to the final score.

The implementation checks candidate education information against available job education requirements.

Experience contributes another 10%.

The current experience scoring provides a simple deterministic compatibility signal rather than attempting to estimate detailed years of experience from unstructured text.

For internship, fresher, student, and entry-level requirements, a candidate without formal experience can still receive full experience compatibility under the implemented rules.

This behavior is intentionally documented as a current deterministic rule rather than a comprehensive experience-understanding model.

---

# 15. Qualification Matching

Qualifications contribute 10% to the final score.

The current implementation performs normalized text-based matching between available candidate information and job qualification requirements.

This provides a lightweight deterministic qualification signal without requiring an additional LLM request.

---

# 16. Retrieval Similarity vs Match Score

The architecture keeps two concepts separate:

### Retrieval similarity

Produced by FAISS during semantic search.

### Match score

Produced by the deterministic matching algorithm.

The retrieval similarity is recorded in the final result but is **not directly included in the current weighted match-score formula**.

Therefore:

```text id="n8c2zz"
RAG similarity
      |
      | candidate discovery
      v
Structured jobs
      |
      v
Deterministic compatibility scoring
      |
      v
Final match score
```

This separation improves interpretability of the matching pipeline.

---

# 17. Agent Prompt Optimization

The specialized agents receive condensed candidate and job context rather than the complete database.

The prompts explicitly emphasize grounding.

The system instructs agents not to invent unsupported:

- Skills
- Employers
- Projects
- Degrees
- Certifications
- Achievements
- Metrics
- Experience

This is particularly important for resume customization, cover-letter generation, interview preparation, and career guidance.

---

# 18. Skill Gap Agent Optimization

The Skill Gap Agent combines deterministic skill comparison with optional LLM explanation.

The deterministic component calculates:

```text id="1f4j1h"
matched required skills
matched preferred skills
missing required skills
missing preferred skills
skill match percentage
```

The LLM can then provide richer explanations and recommendations.

If the LLM call fails, the deterministic skill-gap fallback can still return structured information.

This avoids making basic skill-gap functionality completely dependent on external generation.

---

# 19. Application Agent Optimization

The Application Agent handles:

- Tailored resume generation
- Cover-letter generation

The agent receives candidate and selected-job information and is instructed to prioritize and rephrase genuine information rather than inventing achievements.

A deterministic fallback is available when LLM generation cannot be completed.

This architecture provides:

```text id="l9tq4m"
LLM generation
      |
      +---- success ----> structured generated output
      |
      +---- failure ----> deterministic fallback
```

---

# 20. Interview Agent Optimization

The Interview Agent generates preparation material using:

- Candidate skills
- Candidate projects
- Candidate experience
- Job requirements
- Skill-gap information

The generated questions are divided into:

- Technical
- Resume
- Project
- Role-specific
- HR

The agent also provides deterministic fallback preparation.

Mock-interview answer evaluation similarly attempts LLM evaluation first and falls back to deterministic evaluation when necessary.

---

# 21. Career Assistant Optimization

The Career Assistant does not need the entire application database for every message.

It builds a condensed context containing relevant information such as:

- Candidate name
- Target role
- Skills
- Projects
- Education
- Selected job
- Required skills
- Preferred skills
- Skill-gap information

For conversational continuity, the LLM request includes the most recent six conversation turns.

This limits the amount of historical context sent to the model while retaining recent conversational information.

---

# 22. Deterministic Fallback Architecture

A major resilience optimization is the use of deterministic fallback behavior.

The architecture does not assume that an LLM request will always succeed.

Fallback behavior exists for several AI-assisted functions.

The general design is:

```text id="b5gk5j"
User Request
     |
     v
Agent
     |
     v
LLM Attempt
   /     \
Success   Failure
  |          |
  v          v
LLM       Deterministic
Output      Fallback
   \          /
    \        /
     v      v
    API Response
```

This provides service continuity when an LLM is unavailable, rate-limited, or otherwise fails.

---

# 23. Performance Measurement Method

Performance was measured using:

```text id="7z2g5w"
backend/test_m43_performance.py
```

The test measures response time for the major workflow operations.

An operation is considered successful only when the HTTP response status is in the successful 2xx range.

This prevents HTTP errors such as 404 or 405 from being incorrectly counted as successful performance measurements.

---

# 24. Recorded Performance Results

The recorded M4.3 performance run produced the following timings:

| Operation             | Response time |
| --------------------- | ------------: |
| Health                |       0.010 s |
| RAG job search        |       0.068 s |
| Job matching          |       2.435 s |
| Skill gap             |      24.980 s |
| Resume customization  |      24.017 s |
| Cover letter          |      25.674 s |
| Interview preparation |      24.502 s |
| Career Assistant      |      23.224 s |

Resume upload was also completed successfully during the workflow.

The overall recorded measurements were:

```text id="44g4r5"
Successful operations : 9
Failed operations     : 0
Total time            : 124.909 s
Average               : 15.614 s
Median                : 23.621 s
Fastest               : 0.010 s
Slowest               : 25.674 s
```

The performance test concluded:

```text id="g8z6ha"
M4.3 PERFORMANCE TEST PASSED
```

Pytest reported the performance test as passed.

---

# 25. Performance Bottleneck Analysis

The recorded measurements show three broad performance groups.

## 25.1 Lightweight infrastructure operations

Health checking was extremely fast:

```text id="1n0t3f"
0.010 seconds
```

This represents local API infrastructure overhead rather than AI processing.

## 25.2 RAG and matching

RAG search completed in:

```text id="qj8s4h"
0.068 seconds
```

Job matching completed in:

```text id="i5m1tc"
2.435 seconds
```

These results indicate that the local semantic retrieval and deterministic matching stages were substantially faster than the generation-heavy operations in the recorded test.

## 25.3 Generation-heavy operations

The following operations were approximately 23–26 seconds:

- Skill Gap
- Resume customization
- Cover letter
- Interview preparation
- Career Assistant

These operations involve LLM generation or LLM-dependent processing and therefore represent the dominant latency area in the recorded workflow.

---

# 26. LLM Availability During Performance Testing

During the recorded performance test, the configured Gemini model had reached its available API quota.

The backend therefore logged quota-related errors for some LLM operations and used its fallback behavior.

Despite the LLM quota condition:

```text id="x2v4m9"
9 successful operations
0 failed operations
```

were recorded by the performance test.

This demonstrates the resilience benefit of the fallback architecture.

However, the measured generation times should not be interpreted as pure successful-LLM latency because fallback behavior was involved during the recorded run.

---

# 27. Performance Optimization Opportunities

The current measurements identify several opportunities for future optimization.

### 27.1 Response caching

Frequently repeated RAG queries and stable job information could be cached to avoid repeated processing.

### 27.2 LLM response caching

Repeated requests for the same candidate/job combination could potentially reuse previously generated results where appropriate.

### 27.3 Prompt reduction

Agent prompts can be further optimized by sending only the information required for the current operation.

This can reduce:

- Input tokens
- Network transfer
- LLM processing time
- Cost

### 27.4 Asynchronous processing

Long-running generation operations could be moved to background jobs where appropriate, allowing the API to respond immediately with a processing status.

### 27.5 Batch processing

Embedding and large-scale job processing can be batched when rebuilding or expanding the knowledge base.

### 27.6 Retrieval optimization

As the job database grows, additional filtering or approximate nearest-neighbor indexing strategies could be evaluated.

### 27.7 Database optimization

Additional indexes and query optimization can be introduced if application-tracker data grows significantly.

---

# 28. Scalability Considerations

The current architecture is suitable for the project's current internship knowledge base and development workload.

The current RAG dataset contains:

```text id="5qkz9s"
102 jobs
388 chunks
```

At significantly larger scale, additional engineering may be required.

Potential improvements include:

- Approximate nearest-neighbor FAISS indexes
- Vector database deployment
- Embedding caching
- Batch embedding
- Distributed processing
- API worker scaling
- Background task queues
- Database connection management
- Centralized caching
- LLM request throttling
- Rate-limit handling

These are future scalability options rather than current implemented requirements.

---

# 29. Resource Optimization

The current design reduces unnecessary work through several mechanisms:

1. The FAISS index is built once and loaded for retrieval.
2. Embeddings are normalized and stored.
3. Retrieved chunks are deduplicated by job ID.
4. The retrieval candidate set is bounded.
5. Structured job records are loaded only for retrieved job IDs.
6. Deterministic matching avoids unnecessary LLM calls for the numerical score.
7. Agent conversation history is limited to recent turns.
8. Deterministic fallbacks prevent repeated failure/retry loops from completely breaking the workflow.

---

# 30. Optimization Trade-offs

Optimization requires balancing speed, retrieval coverage, output quality, and implementation complexity.

For example, retrieving more candidate jobs before matching can improve the opportunity to find a suitable result, but increases downstream processing.

Similarly, sending more candidate/job context to an LLM can provide richer grounding but may increase latency and token usage.

The current implementation therefore uses bounded retrieval and condensed agent context as practical compromises for the project's current scale.

---

# 31. Current Performance Assessment

The recorded results indicate that the current system has two distinct performance characteristics:

```text id="xv6y3r"
Local retrieval / deterministic processing
        |
        v
Fast

LLM-dependent generation
        |
        v
Significantly slower
```

The RAG retrieval layer is lightweight in the current dataset, while generation-heavy career-assistance operations account for most of the end-to-end latency.

The system's fallback architecture helps preserve API availability when external model generation is unavailable.

---

# 32. Future Performance Evaluation

Future performance testing should include:

- Concurrent-user load tests.
- Stress testing.
- Large knowledge-base benchmarks.
- RAG latency at different dataset sizes.
- Retrieval latency at different `top_k` values.
- Matching latency with increasing candidate sets.
- LLM token-usage measurements.
- Cold-start vs warm-start measurements.
- Memory usage.
- CPU utilization.
- Database query latency.
- API throughput.
- Production deployment measurements.

Performance targets should be established only after collecting measurements under a representative deployment environment.

---

# 33. Optimization Summary

The M4.3 implementation combines several practical optimization strategies:

| Area                   | Current approach                        |
| ---------------------- | --------------------------------------- |
| Chunking               | Section-based semantic chunks           |
| Embeddings             | `all-MiniLM-L6-v2`                      |
| Vector dimension       | 384                                     |
| Vector search          | FAISS `IndexFlatIP`                     |
| Retrieval              | Bounded `top_k × 3` candidate retrieval |
| Deduplication          | Job ID                                  |
| Matching               | Deterministic weighted scoring          |
| Required skills        | 40%                                     |
| Preferred skills       | 15%                                     |
| Project relevance      | 15%                                     |
| Education              | 10%                                     |
| Experience             | 10%                                     |
| Qualifications         | 10%                                     |
| Agent context          | Condensed candidate/job information     |
| Conversation history   | Recent six turns                        |
| LLM resilience         | Deterministic fallbacks                 |
| Performance validation | Dedicated M4.3 test                     |

---

# 34. Conclusion

The M4.3 optimization work demonstrates that the AI Career Companion Agent uses a combination of semantic retrieval, bounded candidate selection, deterministic scoring, grounded agent prompts, and fallback processing.

The current RAG and deterministic matching layers are relatively lightweight in the tested environment, while LLM-dependent operations represent the primary latency component.

The recorded performance test completed successfully with:

```text id="0a7tqk"
9 successful operations
0 failed operations
124.909 seconds total measured workflow time
M4.3 PERFORMANCE TEST PASSED
```

The current architecture therefore provides a functional baseline for the project's present scale while identifying clear optimization paths for larger datasets, higher concurrency, lower latency, and production deployment.
