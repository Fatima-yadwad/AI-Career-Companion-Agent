import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class InterviewAgent:
    """
    Autonomous Interview Agent for Milestone 3.3.
    Generates tailored interview questions across 5 categories and powers
    the interactive Mock Interview Simulator with multi-metric evaluation.
    """

    def __init__(self):
        self.llm = llm_service

    def generate_interview_prep(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        skill_gap: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates structured interview preparation questions with guides and frameworks.
        """
        job_title = job.get("job_title", "Position")
        company = job.get("company", "Company")

        candidate_summary = {
            "name": candidate.get("full_name", "Candidate"),
            "skills": list(candidate.get("skills", [])),
            "education": candidate.get("education", []),
            "experience": candidate.get("experience", []),
            "projects": candidate.get("projects", []),
        }

        job_summary = {
            "title": job_title,
            "company": company,
            "required_skills": list(job.get("required_skills", [])),
            "preferred_skills": list(job.get("preferred_skills", [])),
            "responsibilities": list(job.get("responsibilities", [])),
        }

        system_instruction = (
            "You are an expert Technical Interview Coach and Interview Preparation Agent. "
            "Generate insightful, role-specific interview preparation questions for the candidate. "
            "Base technical questions on the job requirements. "
            "Base resume and project questions strictly on the candidate's actual projects and experience. "
            "Include actionable preparation guides and answer frameworks for every question."
        )

        prompt = f"""
Generate a comprehensive interview question set for this candidate and target role.

CANDIDATE:
{json.dumps(candidate_summary, indent=2)}

TARGET JOB:
{json.dumps(job_summary, indent=2)}

SKILL GAP CONTEXT:
{json.dumps(skill_gap or {}, indent=2)}

Return a valid JSON object matching this schema:
{{
  "job_title": "{job_title}",
  "company": "{company}",
  "technical_questions": [
    {{
      "id": "tech_1",
      "category": "Technical",
      "question": "Question text based on required technologies",
      "preparation_guide": "How to structure thinking, core concepts to recall",
      "suggested_topics": ["Topic 1", "Topic 2"],
      "sample_answer_framework": "Step 1: Define... Step 2: Explain trade-offs... Step 3: Example"
    }}
  ],
  "resume_questions": [
    {{
      "id": "resume_1",
      "category": "Resume",
      "question": "Question probing specific skills/experience on resume",
      "preparation_guide": "How to articulate personal background smoothly",
      "suggested_topics": ["Topic 1", "Topic 2"],
      "sample_answer_framework": "STAR method framework"
    }}
  ],
  "project_questions": [
    {{
      "id": "proj_1",
      "category": "Projects",
      "question": "Question specifically about candidate's real project",
      "preparation_guide": "How to explain project architecture and challenges",
      "suggested_topics": ["Architecture", "Obstacles overcome"],
      "sample_answer_framework": "Problem -> Solution -> Impact structure"
    }}
  ],
  "role_specific_questions": [
    {{
      "id": "role_1",
      "category": "Role Specific",
      "question": "Scenario or responsibility question relevant to {job_title}",
      "preparation_guide": "How to demonstrate day-to-day role competence",
      "suggested_topics": ["Best practices", "Collaboration"],
      "sample_answer_framework": "Methodology outline"
    }}
  ],
  "hr_questions": [
    {{
      "id": "hr_1",
      "category": "HR & Behavioral",
      "question": "e.g. Tell me about yourself / Why {company}?",
      "preparation_guide": "How to present enthusiasm, values, and cultural fit",
      "suggested_topics": ["Career motivation", "Company mission"],
      "sample_answer_framework": "Present -> Past -> Future structure"
    }}
  ]
}}
"""

        try:
            result = self.llm.generate_structured(
                prompt=prompt, system_instruction=system_instruction
            )
            result["source"] = "interview_agent_llm"
            return result
        except Exception as error:
            logger.warning(
                f"LLM interview prep generation failed: {error}. Using deterministic fallback."
            )
            return self._build_deterministic_prep(candidate_summary, job_summary)

    def evaluate_mock_answer(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        question: str,
        answer: str,
        category: str = "Technical",
    ) -> Dict[str, Any]:
        """
        Evaluates a candidate's mock interview answer using a multi-metric rubric.
        """
        if not answer or len(answer.strip()) < 5:
            return {
                "overall_score": 15,
                "technical_understanding": {"score": 1, "feedback": "Answer is too short or empty to assess."},
                "relevance": {"score": 1, "feedback": "Please provide a detailed response addressing the question."},
                "clarity": {"score": 2, "feedback": "Answer was too brief."},
                "completeness": {"score": 1, "feedback": "Key concepts and examples were omitted."},
                "project_understanding": {"score": 2, "feedback": "No project or implementation details given."},
                "what_went_well": ["Attempted to submit an answer."],
                "areas_for_improvement": ["Elaborate on the technical solution, tools used, and personal experience."],
                "suggested_answer_structure": "1. Direct answer\n2. Key technical concepts\n3. Real-world example\n4. Conclusion",
                "source": "deterministic_eval",
            }

        prompt = f"""
You are an expert Technical Interview Evaluator.
Evaluate the candidate's answer to the interview question below for the position of {job.get('job_title', 'Role')} at {job.get('company', 'Company')}.

QUESTION ({category}):
"{question}"

CANDIDATE ANSWER:
"{answer}"

CANDIDATE PROFILE HIGHLIGHTS:
Skills: {candidate.get('skills', [])}
Projects: {candidate.get('projects', [])}

Evaluate the response objectively across 5 criteria (scores 1-10 each):
1. Technical Understanding: Accurate use of terms, fundamental correctness.
2. Relevance: Directness and adherence to the prompt.
3. Clarity: Articulation, structure, communication quality.
4. Completeness: Thorough coverage of core aspects and edge cases.
5. Project Understanding: Depth in explaining engineering decisions and trade-offs.

Return a valid JSON object matching this schema:
{{
  "overall_score": 85,
  "technical_understanding": {{
    "score": 8,
    "feedback": "Specific assessment of technical concepts mentioned"
  }},
  "relevance": {{
    "score": 9,
    "feedback": "How well the answer addressed the specific question"
  }},
  "clarity": {{
    "score": 8,
    "feedback": "Feedback on communication style and organization"
  }},
  "completeness": {{
    "score": 8,
    "feedback": "Feedback on depth and missing nuances"
  }},
  "project_understanding": {{
    "score": 8,
    "feedback": "Feedback on practical implementation insight"
  }},
  "what_went_well": [
    "Strength point 1",
    "Strength point 2"
  ],
  "areas_for_improvement": [
    "Improvement recommendation 1",
    "Improvement recommendation 2"
  ],
  "suggested_answer_structure": "A concise outline demonstrating how to structure a top-tier answer for this question."
}}
"""

        try:
            result = self.llm.generate_structured(prompt=prompt, temperature=0.1)
            result["source"] = "interview_agent_llm"
            return result
        except Exception as error:
            logger.warning(
                f"LLM mock answer evaluation failed: {error}. Using deterministic evaluation."
            )
            return self._build_deterministic_eval(question, answer)

    def _build_deterministic_prep(
        self, candidate: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deterministic question bank fallback.
        """
        job_title = job.get("title", "Position")
        company = job.get("company", "Company")
        skills = job.get("required_skills", []) or ["Python", "Problem Solving"]
        cand_projects = candidate.get("projects", [])

        tech_qs = []
        for i, skill in enumerate(skills[:4], start=1):
            tech_qs.append(
                {
                    "id": f"tech_{i}",
                    "category": "Technical",
                    "question": f"Explain your experience with {skill} and describe how you have applied it in real-world scenarios.",
                    "preparation_guide": f"Review core principles of {skill}, key libraries/APIs, and performance considerations.",
                    "suggested_topics": [f"{skill} fundamentals", "Best practices", "Error handling"],
                    "sample_answer_framework": f"1. Define {skill} background -> 2. Walk through a specific code use case -> 3. Discuss optimization/debugging.",
                }
            )

        proj_qs = []
        for i, proj in enumerate(cand_projects[:3], start=1):
            p_name = proj.get("name", str(proj)) if isinstance(proj, dict) else str(proj)
            proj_qs.append(
                {
                    "id": f"proj_{i}",
                    "category": "Projects",
                    "question": f"In your project '{p_name}', what were the biggest technical challenges you faced and how did you resolve them?",
                    "preparation_guide": "Use the STAR method (Situation, Task, Action, Result) to describe engineering problem solving.",
                    "suggested_topics": ["Architecture design", "Data handling", "Performance bottlenecks"],
                    "sample_answer_framework": "Situation: What was the goal -> Task: The challenge -> Action: Your solution -> Result: Measurable outcome.",
                }
            )

        if not proj_qs:
            proj_qs.append(
                {
                    "id": "proj_1",
                    "category": "Projects",
                    "question": "Describe the most complex software project you have built. How did you design its architecture?",
                    "preparation_guide": "Focus on modular design, choice of tools, and testing.",
                    "suggested_topics": ["Architecture", "Tool selection", "Testing"],
                    "sample_answer_framework": "Overview -> Key Components -> Results.",
                }
            )

        resume_qs = [
            {
                "id": "resume_1",
                "category": "Resume",
                "question": f"Walking through your resume, what has been your most impactful technical achievement so far?",
                "preparation_guide": "Highlight hands-on problem solving, consistency, and passion for continuous learning.",
                "suggested_topics": ["Core technical skills", "Self-learning", "Project delivery"],
                "sample_answer_framework": "Context -> Core skill applied -> Outcome.",
            },
            {
                "id": "resume_2",
                "category": "Resume",
                "question": "How do you stay updated with emerging tools and frameworks in modern software development?",
                "preparation_guide": "Mention documentation, open source, tech blogs, and building experiments.",
                "suggested_topics": ["Documentation", "GitHub", "Hands-on projects"],
                "sample_answer_framework": "Daily/weekly habits -> Applied learnings in code.",
            },
        ]

        role_qs = [
            {
                "id": "role_1",
                "category": "Role Specific",
                "question": f"What excites you most about the {job_title} role at {company}?",
                "preparation_guide": "Connect your technical skills with company goals and projects.",
                "suggested_topics": ["Company vision", "Role responsibilities", "Personal growth"],
                "sample_answer_framework": "Skill match -> Company admiration -> Career vision.",
            }
        ]

        hr_qs = [
            {
                "id": "hr_1",
                "category": "HR & Behavioral",
                "question": "Tell me about yourself and your journey into technology.",
                "preparation_guide": "Keep it under 2 minutes: current status, key skills, relevant projects, future goals.",
                "suggested_topics": ["Current education", "Key skills", "Why this role"],
                "sample_answer_framework": "Present -> Past -> Future.",
            },
            {
                "id": "hr_2",
                "category": "HR & Behavioral",
                "question": "Describe a situation where you had to learn a completely new technology under tight deadlines.",
                "preparation_guide": "Demonstrate agility, resourcefulness, and systematic learning.",
                "suggested_topics": ["Learning curve", "Time management", "Execution"],
                "sample_answer_framework": "STAR method.",
            },
        ]

        return {
            "job_title": job_title,
            "company": company,
            "technical_questions": tech_qs,
            "resume_questions": resume_qs,
            "project_questions": proj_qs,
            "role_specific_questions": role_qs,
            "hr_questions": hr_qs,
            "source": "interview_agent_deterministic",
        }

    def _build_deterministic_eval(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Deterministic evaluator fallback.
        """
        words = len(answer.split())
        base_score = min(90, max(40, int(words * 0.8) + 30))

        return {
            "overall_score": base_score,
            "technical_understanding": {
                "score": min(9, max(5, int(base_score / 10))),
                "feedback": "Demonstrates foundational conceptual knowledge in response.",
            },
            "relevance": {
                "score": min(9, max(6, int(base_score / 10) + 1)),
                "feedback": "Directly addresses the prompt and maintains focus.",
            },
            "clarity": {
                "score": min(9, max(5, int(base_score / 10))),
                "feedback": "Clear phrasing with structured thoughts.",
            },
            "completeness": {
                "score": min(8, max(4, int(base_score / 10))),
                "feedback": "Covers essential points; consider adding concrete metrics or examples.",
            },
            "project_understanding": {
                "score": min(9, max(5, int(base_score / 10))),
                "feedback": "Good application perspective shown.",
            },
            "what_went_well": [
                "Clearly addressed the core concept.",
                "Maintained professional and confident tone.",
            ],
            "areas_for_improvement": [
                "Include a specific architectural or real-world example.",
                "Discuss how you handled edge cases or trade-offs.",
            ],
            "suggested_answer_structure": (
                "1. State direct thesis / concept definition\n"
                "2. Provide concrete technical illustration / code design\n"
                "3. Highlight trade-offs and performance\n"
                "4. Conclude with relevance to the role."
            ),
            "source": "deterministic_eval",
        }


# Singleton instance
interview_agent = InterviewAgent()
