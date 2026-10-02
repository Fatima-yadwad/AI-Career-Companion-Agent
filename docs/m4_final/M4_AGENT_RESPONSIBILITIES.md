# AI Career Companion Agent

## Milestone 4.4 – Agent Responsibilities and Multi-Agent Architecture

**Project:** AI Career Companion Agent
**Milestone:** M4.4 – Documentation and Final Integration

---

# 1. Overview

The AI Career Companion Agent uses specialized Python agent modules to provide different career-support capabilities.

The current agent layer contains four primary agents:

1. **Skill Gap Agent**
2. **Application Agent**
3. **Interview Agent**
4. **Career Assistant**

Each agent has a focused responsibility and receives structured candidate/job information from the FastAPI application.

The agents are implemented as Python service classes and are not dependent on a separate external agent orchestration framework.

The architecture uses a combination of:

- Deterministic processing
- Structured prompts
- LLM generation
- Structured JSON responses
- Deterministic fallback behavior
- Candidate/job grounding

This design allows the system to provide specialized career functions while maintaining consistency with the candidate's stored profile.

---

# 2. Agent Architecture

```text
                         FastAPI Backend
                              |
                              v
                     Candidate / Job Context
                              |
        +---------------------+----------------------+
        |                     |                      |
        v                     v                      v
+---------------+      +---------------+      +---------------+
| Skill Gap     |      | Application   |      | Interview     |
| Agent         |      | Agent         |      | Agent         |
+-------+-------+      +-------+-------+      +-------+-------+
        |                      |                      |
        v                      v                      v
 Skill Analysis          Resume / Cover         Interview Prep /
                         Letter Generation       Mock Evaluation
        |                      |                      |
        +----------------------+----------------------+
                               |
                               v
                     +--------------------+
                     | Career Assistant   |
                     +---------+----------+
                               |
                               v
                     Context-aware Career
                         Conversation
```

---

# 3. Agent Design Principles

The agent layer follows the following principles.

## 3.1 Specialized responsibilities

Each agent is responsible for a specific career-support function instead of placing all functionality into a single large agent.

## 3.2 Grounded candidate information

Agent prompts are supplied with structured information extracted from the candidate profile.

The agents are instructed not to invent unsupported candidate information.

## 3.3 Structured generation

Where LLM generation is used, the agents request structured JSON responses.

This makes generated results easier for the FastAPI layer to process.

## 3.4 Deterministic foundation

Important calculations, particularly skill matching, are performed deterministically.

## 3.5 Fallback behavior

Each major agent capability has deterministic fallback logic so that the application can continue operating when the LLM is unavailable or rate-limited.

---

# 4. Skill Gap Agent

**Implementation:** `backend/agents/skill_gap_agent.py`

## 4.1 Responsibility

The Skill Gap Agent analyzes the difference between the candidate's current skills and the skills required or preferred for a selected job.

Its purpose is to answer:

- Which required skills does the candidate already have?
- Which required skills are missing?
- Which preferred skills are already available?
- Which preferred skills are missing?
- What areas should the candidate improve?

---

## 4.2 Inputs

The agent receives:

### Candidate information

- Name
- Target role
- Skills
- Education
- Experience
- Projects
- Certifications

### Job information

- Job ID
- Job title
- Company
- Location
- Work type
- Description
- Required skills
- Preferred skills
- Qualifications
- Responsibilities
- Experience requirements
- Education requirements

---

## 4.3 Deterministic Skill Analysis

Before LLM generation, the agent uses deterministic matching helpers to compare candidate and job skills.

The calculation distinguishes:

```text
Candidate Skills
       |
       +--------------------+
       |                    |
       v                    v
Required Skills        Preferred Skills
       |                    |
       v                    v
Matched / Missing      Matched / Missing
```

The skill match percentage is calculated from the matched required and preferred skills relative to the unique required and preferred skill set.

If no skills are specified by the job, the implementation treats the skill match as 100%.

---

# 5. Skill Gap Agent Output

The LLM response can contain:

- Job title
- Company
- Summary
- Strong matches
- Critical gaps
- Partial gaps
- Preferred gaps
- Experience gaps
- Qualification gaps
- Recommendations

The deterministic fields are also injected into the final result:

- Skill match percentage
- Matched skills
- Missing skills
- Job title
- Company
- Source

The source identifies whether the result was produced through the LLM or deterministic fallback.

Example source values:

```text
skill_gap_agent_llm
skill_gap_agent_deterministic
```

---

# 6. Skill Gap Grounding

The Skill Gap Agent uses an evidence packet containing the candidate's actual information and a corresponding job evidence packet.

The LLM is instructed to:

- Use only supplied candidate information
- Distinguish required from preferred skills
- Avoid unsupported claims
- Report missing evidence explicitly
- Avoid inventing experience or qualifications

When evidence is unavailable, the intended response is equivalent to:

**"No evidence found in profile."**

This prevents the agent from treating an absence of information as proof that the candidate possesses a skill or qualification.

---

# 7. Skill Gap Fallback

If LLM generation fails, the agent uses deterministic fallback logic.

The fallback can produce:

- Strong skill matches
- Critical required-skill gaps
- Preferred-skill gaps
- Basic experience information
- Qualification information
- Recommendations for missing required skills

Recommendations can suggest focused learning and practical project/demo work.

The fallback source is:

`skill_gap_agent_deterministic`

This allows the API to return useful structured output even when LLM generation is unavailable.

---

# 8. Application Agent

**Implementation:** `backend/agents/application_agent.py`

The Application Agent supports two major functions:

1. Resume customization
2. Cover letter generation

Its purpose is to help the candidate adapt application materials to a selected job without fabricating candidate information.

---

# 9. Resume Customization

## 9.1 Inputs

The agent receives candidate information including:

- Contact information
- Target role
- Summary
- Skills
- Education
- Experience
- Projects
- Certifications

The selected job provides:

- Job title
- Company
- Location
- Description
- Required skills
- Preferred skills
- Responsibilities

---

## 9.2 Resume Customization Process

```text
Candidate Profile
       |
       v
Selected Job
       |
       v
Compare Candidate Skills
with Job Requirements
       |
       v
Prioritize Relevant Information
       |
       v
LLM Resume Customization
       |
       v
Structured Tailored Resume
```

The agent is instructed to prioritize, rephrase and highlight genuine candidate information rather than creating new qualifications.

---

# 10. Customized Resume Output

The generated result can contain:

- Job title
- Company
- Contact information
- Professional summary
- Highlighted skills
- Projects
- Experience
- Education
- Certifications
- Suggested keywords
- Customization strategy

The agent can identify job-related keywords that the candidate may study or incorporate when genuinely applicable.

---

# 11. Resume Grounding Rules

The Application Agent is explicitly instructed not to invent:

- Skills
- Employers
- Project names
- Degrees
- Certifications
- Metrics
- Achievements
- Experience

The agent may instead:

- Reorder existing skills
- Highlight relevant projects
- Rephrase existing experience
- Prioritize job-relevant information
- Suggest keywords for future learning

This is important for maintaining factual integrity in application documents.

---

# 12. Resume Deterministic Fallback

If LLM generation fails, the Application Agent creates a deterministic customized resume.

The fallback:

- Prioritizes candidate skills that match required job skills
- Preserves candidate projects
- Preserves education
- Preserves certifications
- Preserves available experience
- Generates a basic professional summary
- Provides selected job-related keywords

The fallback does not require an active LLM connection.

Source:

`application_agent_deterministic`

---

# 13. Cover Letter Generation

The Application Agent also generates a job-specific cover letter.

The input includes:

### Candidate

- Name
- Contact information
- Skills
- Education
- Experience
- Projects

### Job

- Job title
- Company
- Location
- Description
- Required skills

---

# 14. Cover Letter Output

The LLM response can contain:

- Subject
- Salutation
- Opening
- Skills alignment
- Project alignment
- Company fit
- Closing
- Sign-off
- Complete letter

The generated letter is intended to connect the candidate's actual background with the selected job.

---

# 15. Cover Letter Grounding

The cover letter prompt explicitly prevents unsupported claims.

The agent should not create:

- Fake employment
- Fake project experience
- Fake achievements
- Unsupported technical expertise
- Unsupported company relationships

The candidate's supplied profile remains the primary evidence source.

---

# 16. Cover Letter Fallback

A deterministic cover-letter template is available when LLM generation fails.

The fallback uses available:

- Candidate name
- Skills
- Project information
- Job title
- Company

The fallback source is:

`application_agent_deterministic`

The fallback should be treated as a template-based generation path rather than a substitute for verified candidate-specific reasoning.

---

# 17. Interview Agent

**Implementation:** `backend/agents/interview_agent.py`

The Interview Agent provides interview preparation and mock-answer evaluation.

It has two major functions:

1. Interview preparation generation
2. Mock interview answer evaluation

---

# 18. Interview Preparation

## 18.1 Inputs

Candidate context includes:

- Name
- Skills
- Education
- Experience
- Projects
- Summary

Job context includes:

- Job title
- Company
- Required skills
- Preferred skills
- Responsibilities

Skill-gap information may also be provided.

---

# 19. Interview Question Categories

The Interview Agent generates questions across five categories:

| Category      | Purpose                                                 |
| ------------- | ------------------------------------------------------- |
| Technical     | Test job-relevant technical knowledge                   |
| Resume        | Discuss information contained in the candidate's resume |
| Project       | Explore actual candidate projects                       |
| Role-specific | Test understanding related to the selected role         |
| HR            | Practice behavioral/interpersonal questions             |

The requested output can include:

- Question ID
- Category
- Question
- Preparation guide
- Suggested topics
- Sample answer framework

---

# 20. Interview Grounding

Technical questions are based on the job requirements.

Resume and project questions are based on information actually present in the candidate profile.

The agent is instructed not to introduce fictional projects or experience.

This is particularly important for interview preparation because fabricated resume content could cause inconsistencies during an actual interview.

---

# 21. Deterministic Interview Fallback

When LLM generation is unavailable, the Interview Agent creates deterministic questions.

The fallback can generate:

- Up to four technical questions from required skills
- Questions related to candidate projects
- Resume questions
- Role-specific questions
- HR questions

If the candidate has no projects, the fallback uses a generic project-oriented question rather than inventing a project.

Source:

`interview_agent_deterministic`

---

# 22. Mock Interview Evaluation

The Interview Agent also evaluates candidate answers.

The evaluation accepts:

- Candidate information
- Job information
- Interview question
- Candidate answer
- Question category

The LLM evaluates five criteria:

1. Technical understanding
2. Relevance
3. Clarity
4. Completeness
5. Project understanding

Each criterion uses a 1–10 scoring scale.

The response can include:

- Overall score
- Criterion scores
- Positive feedback
- Areas for improvement
- Suggested answer framework

---

# 23. Empty Answer Handling

The system also handles empty or extremely short mock interview answers.

If an answer is empty or fewer than five characters, the agent returns a deterministic low-score structured evaluation instead of attempting unnecessary LLM generation.

This provides predictable behavior for invalid or incomplete input.

---

# 24. Mock Evaluation Fallback

For valid answers, if LLM evaluation fails, the deterministic evaluator estimates a basic score using answer length and provides structured feedback.

The deterministic evaluator considers answer length as a simple proxy for completeness.

It should therefore be considered a fallback evaluation mechanism rather than a full semantic interview assessment.

---

# 25. Career Assistant

**Implementation:** `backend/agents/career_assistant.py`

The Career Assistant provides conversational career guidance.

Unlike the specialized task agents, it is designed for multi-turn interaction.

It can respond to questions about:

- Skill development
- Learning plans
- Resume improvement
- Interview preparation
- Job matching
- Career planning
- Selected internship/job opportunities

---

# 26. Career Assistant Context

The assistant can receive:

### Candidate context

- Name
- Target role
- Skills
- Projects
- Education

### Selected job context

- Job title
- Company
- Required skills
- Preferred skills

### Skill gap context

- Matched skills
- Missing skills
- Match score

### Conversation context

- Recent conversation history

The implementation includes the latest six conversation turns in the LLM prompt.

---

# 27. Career Assistant Conversation Flow

```text
User Message
      |
      v
Load Profile Context
      |
      v
Load Selected Job Context
      |
      v
Load Skill Gap Context
      |
      v
Load Recent Conversation History
      |
      v
Construct Grounded Prompt
      |
      v
LLM Career Response
      |
      v
Suggested Follow-ups
      |
      v
Persist Conversation
```

---

# 28. Career Assistant Response Types

The assistant adapts its response based on the user's question.

For skill/learning questions, it can provide:

- Learning roadmap
- Missing skills
- Existing strengths
- Suggested next steps

For resume questions, it can provide:

- Resume strategy
- Relevant skills
- Project highlighting suggestions
- Impact/quantification guidance

For interview questions, it can provide:

- Preparation strategy
- Required skills to revise
- STAR-style response guidance
- Company research suggestions

For general career questions, it provides practical career guidance based on the available context.

---

# 29. Career Assistant Grounding

The system prompt instructs the Career Assistant to:

- Use the candidate profile
- Use selected job information
- Use available skill-gap information
- Avoid inventing previous experiences
- Provide practical and concise advice
- Reference known strengths and gaps when relevant

This makes the assistant profile-aware instead of behaving as a completely generic chatbot.

---

# 30. Career Assistant Fallback

A deterministic response builder is available when LLM generation fails.

The fallback identifies common user intents such as:

- Skills/learning/gaps
- Resume/projects
- Interview preparation
- General career guidance

It then generates an appropriate structured response.

Source:

`career_assistant_deterministic`

---

# 31. Agent-to-Agent Data Consistency

The agents share a common structured representation of the candidate and selected job.

The overall information flow is:

```text
                   Candidate Profile
                          |
              +-----------+-----------+
              |                       |
              v                       v
         Matching Service        Career Agents
              |                       |
              v                       v
        Selected Job            Agent Context
              |                       |
              +-----------+-----------+
                          |
         +----------------+----------------+
         |                |                |
         v                v                v
    Skill Gap       Application       Interview
       Agent           Agent            Agent
         |                |                |
         +----------------+----------------+
                          |
                          v
                  Career Assistant
```

The same underlying candidate information is used across capabilities to reduce contradictions.

---

# 32. Multi-Agent Consistency Rules

The following consistency principles are used:

### Candidate consistency

Agents should use the same stored candidate skills, education, experience and projects.

### Job consistency

Agents should use the selected job's structured requirements.

### Skill-gap consistency

Application and interview preparation can use the same skill-gap information produced for the selected job.

### Grounding consistency

No agent should introduce unsupported candidate facts.

### Output consistency

Structured JSON responses provide predictable interfaces for the FastAPI layer.

---

# 33. LLM and Fallback Relationship

The agent architecture follows:

```text
                    Agent Input
                        |
                        v
              Deterministic Context
                        |
                        v
                LLM Generation
                   /       \
              Success       Failure
                |             |
                v             v
           LLM Response   Deterministic
                            Fallback
                |             |
                +------+------+
                       |
                       v
                Structured Output
```

This architecture means the application is not completely dependent on successful LLM calls for every workflow step.

---

# 34. Agent Source Identification

Agent responses identify their generation path where applicable.

Typical source values include:

```text
skill_gap_agent_llm
skill_gap_agent_deterministic

application_agent_llm
application_agent_deterministic

interview_agent_llm
interview_agent_deterministic

career_assistant_llm
career_assistant_deterministic

deterministic_eval
```

This provides useful information when evaluating system behavior and debugging LLM availability issues.

---

# 35. Agent Responsibilities Summary

| Agent             | Primary Responsibility                         | Main Output                                  |
| ----------------- | ---------------------------------------------- | -------------------------------------------- |
| Skill Gap Agent   | Compare candidate skills with job requirements | Skill gaps and recommendations               |
| Application Agent | Tailor application materials                   | Customized resume and cover letter           |
| Interview Agent   | Prepare and evaluate interviews                | Questions, preparation and answer evaluation |
| Career Assistant  | Provide conversational career guidance         | Context-aware career responses               |

---

# 36. Relationship With RAG and Matching

The agents do not independently replace the RAG or matching systems.

The architecture separates responsibilities:

```text
RAG
 |
 +--> Finds semantically relevant jobs
 |
 v
Matching Service
 |
 +--> Calculates candidate-job compatibility
 |
 v
Selected Job
 |
 +--> Skill Gap Agent
 +--> Application Agent
 +--> Interview Agent
 +--> Career Assistant
```

Therefore:

- RAG is responsible for semantic job retrieval.
- Matching Service is responsible for deterministic compatibility scoring.
- Agents provide specialized career assistance using the resulting candidate/job context.

---

# 37. Reliability and Failure Handling

Agent operations can encounter:

- LLM quota limitations
- Network/API failures
- Invalid input
- Missing candidate information
- Missing job information
- Empty answers

The implementation provides deterministic fallback paths for major functions.

This design was also exercised during M4.3 performance testing, where LLM quota limitations occurred but the API workflow continued successfully through fallback behavior.

---

# 38. Security and Privacy Considerations

Agent context is constructed from the authenticated user's profile and selected application/job data.

The system should maintain:

- User/profile ownership checks
- Authentication requirements
- User-specific conversation history
- User-specific application records

The agents should only use candidate information available through the authorized application context.

---

# 39. Current Limitations

The current agent implementation has several limitations.

1. Some fallback responses are template-based.
2. Deterministic interview evaluation uses relatively simple answer-length heuristics.
3. Experience and qualification analysis can be simplified when using deterministic fallback logic.
4. LLM output quality depends on model availability and quota.
5. Conversation context is limited to recent turns in the LLM prompt.
6. The agents are implemented as specialized Python modules rather than independent autonomous services.
7. The current system does not use a dedicated multi-agent orchestration framework.

These limitations are documented as opportunities for future development.

---

# 40. Future Improvements

Potential improvements include:

- Stronger structured-output validation
- More advanced candidate evidence tracking
- Better experience-level reasoning
- Improved qualification matching
- Semantic mock-answer evaluation
- Long-term conversational memory
- Agent response evaluation
- Automated hallucination checks
- Agent observability and tracing
- More sophisticated multi-agent orchestration if required
- Better fallback templates
- Candidate-specific learning recommendations
- Automated consistency checks between generated resume and interview preparation

---

# 41. Conclusion

The AI Career Companion Agent uses four specialized agent modules to support different stages of the student career journey.

The **Skill Gap Agent** identifies the difference between candidate capabilities and job requirements.

The **Application Agent** adapts genuine candidate information into job-specific resume and cover-letter content.

The **Interview Agent** generates grounded interview preparation and evaluates mock answers.

The **Career Assistant** provides conversational, profile-aware career guidance.

Together with the RAG retrieval and deterministic matching layers, these agents form a modular career-support architecture that prioritizes grounded information, structured outputs, reliability and reuse of the candidate's actual profile data.
