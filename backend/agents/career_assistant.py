import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class CareerAssistant:
    """
    Context-Aware Conversational Career Assistant for Milestone 3.4.
    Maintains multi-turn context across student profile, target jobs,
    skill gap analysis, and interview preparation.
    """

    def __init__(self):
        self.llm = llm_service

    def chat(
        self,
        message: str,
        profile: Optional[Dict[str, Any]] = None,
        job: Optional[Dict[str, Any]] = None,
        skill_gap: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Processes a conversation turn given structured context and history.
        """
        history = history or []
        profile = profile or {}
        job = job or {}
        skill_gap = skill_gap or {}

        # Prepare condensed context
        context_summary = {
            "candidate_name": profile.get("full_name", "Student"),
            "target_role": profile.get("target_role", ""),
            "skills": profile.get("skills", []),
            "projects": [
                p.get("name", str(p)) if isinstance(p, dict) else str(p)
                for p in profile.get("projects", [])
            ],
            "education": profile.get("education", []),
            "selected_job": {
                "job_title": job.get("job_title"),
                "company": job.get("company"),
                "required_skills": job.get("required_skills", []),
                "preferred_skills": job.get("preferred_skills", []),
            }
            if job
            else None,
            "skill_gap_summary": {
                "matched_skills": skill_gap.get("matched_skills", []),
                "missing_skills": skill_gap.get("missing_skills", []),
                "match_score": skill_gap.get("skill_match_percentage")
                or skill_gap.get("match_score"),
            }
            if skill_gap
            else None,
        }

        system_instruction = (
            "You are CareerCompanion AI, an empathetic, highly intelligent, and practical career advisor. "
            "You help students and early-career engineers navigate their career trajectory, prepare for roles, "
            "understand skill gaps, customize resumes, and prepare for interviews. "
            "CRITICAL RULES: "
            "1. Ground all specific advice in the student's actual profile facts and the selected job context. "
            "2. Never invent fake past experiences for the student. "
            "3. Be encouraging, concise, actionable, and structured with bullet points where helpful. "
            "4. If asked about a skill or job, reference their actual match/gap data whenever available."
        )

        # Build formatted dialogue history
        history_text = ""
        for turn in history[-6:]:
            role = "User" if turn.get("role") == "user" else "Assistant"
            history_text += f"{role}: {turn.get('content')}\n"

        prompt = f"""
CONTEXT AVAILABLE TO YOU:
{json.dumps(context_summary, indent=2)}

RECENT CONVERSATION HISTORY:
{history_text}

USER MESSAGE:
"{message}"

Respond helpfully and intelligently to the user.
Return a valid JSON object matching this schema:
{{
  "message": "Your complete Markdown formatted response to the user.",
  "suggested_followups": [
    "Suggested follow-up question 1",
    "Suggested follow-up question 2",
    "Suggested follow-up question 3"
  ]
}}
"""

        try:
            result = self.llm.generate_structured(
                prompt=prompt, system_instruction=system_instruction, temperature=0.2
            )
            return {
                "message": result.get("message", "I am here to help you advance your career!"),
                "suggested_followups": result.get(
                    "suggested_followups",
                    [
                        "What should I learn first?",
                        "How can I tailor my resume for this role?",
                        "What interview questions might I face?",
                    ],
                ),
                "context_used": {
                    "profile": bool(profile),
                    "job": bool(job),
                    "skill_gap": bool(skill_gap),
                    "history_turns": len(history),
                },
                "source": "career_assistant_llm",
            }
        except Exception as error:
            logger.warning(
                f"LLM career assistant failed: {error}. Using deterministic fallback."
            )
            return self._build_deterministic_response(
                message=message,
                profile=profile,
                job=job,
                skill_gap=skill_gap,
            )

    def _build_deterministic_response(
        self,
        message: str,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        skill_gap: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deterministic, helpful career advisory fallback.
        """
        msg_lower = message.lower()
        job_title = job.get("job_title", "your target role")
        company = job.get("company", "the target company")
        skills = profile.get("skills", [])
        missing = skill_gap.get("missing_skills", [])
        matched = skill_gap.get("matched_skills", [])

        if "skill" in msg_lower or "learn" in msg_lower or "study" in msg_lower or "gap" in msg_lower:
            if missing:
                response = (
                    f"### Recommended Learning Roadmap for **{job_title}**\n\n"
                    f"Based on your gap analysis, here are the top skills you should prioritize:\n\n"
                    + "\n".join([f"- **{s}**: Focus on hands-on project implementation and API integration." for s in missing[:4]])
                    + f"\n\n**Your Current Strengths:** You already match key requirements including `{', '.join(matched[:4])}`. "
                    "Building a portfolio project combining these strengths with your target skills will make your application stand out!"
                )
            else:
                response = (
                    f"You have excellent skill coverage for **{job_title}**! "
                    f"Focus on deepening your expertise in `{', '.join(skills[:5])}` through architecture design and performance optimization."
                )
        elif "resume" in msg_lower or "highlight" in msg_lower or "project" in msg_lower:
            projects = profile.get("projects", [])
            proj_text = (
                f"Specifically, highlight **'{projects[0]}'**"
                if projects
                else "Focus on your practical coding and engineering projects"
            )
            response = (
                f"### Resume Strategy for **{job_title}** at **{company}**\n\n"
                f"1. **Lead with Matching Skills:** Ensure `{', '.join(matched[:5]) if matched else ', '.join(skills[:5])}` appear in the top skills section.\n"
                f"2. **Spotlight Core Projects:** {proj_text} at the top of your projects section.\n"
                "3. **Quantify Impact:** Detail the technical architecture, frameworks used, and problems solved."
            )
        elif "interview" in msg_lower or "prepare" in msg_lower:
            response = (
                f"### Interview Strategy for **{job_title}**\n\n"
                f"1. **Core Technicals:** Expect questions on `{', '.join(job.get('required_skills', skills)[:4])}`.\n"
                "2. **Project Walkthrough:** Be ready to describe your project architecture using the **STAR method**.\n"
                f"3. **Role Alignment:** Research {company}'s products and prepare questions on team engineering practices."
            )
        else:
            response = (
                f"Hello {profile.get('full_name', 'there')}! I'm your AI Career Copilot. "
                f"I'm tracking your progress for **{job_title}** at **{company}**.\n\n"
                "You can ask me to:\n"
                "- Break down your **skill gaps** and create a learning roadmap.\n"
                "- Help customize your **resume** and **cover letter**.\n"
                "- Practice **mock interview questions** with instant feedback.\n"
                "- Compare different internship opportunities."
            )

        return {
            "message": response,
            "suggested_followups": [
                "What skills should I learn first?",
                "How can I tailor my resume?",
                "Give me interview prep tips.",
            ],
            "context_used": {
                "profile": bool(profile),
                "job": bool(job),
                "skill_gap": bool(skill_gap),
                "history_turns": 0,
            },
            "source": "career_assistant_deterministic",
        }


# Singleton instance
career_assistant = CareerAssistant()
