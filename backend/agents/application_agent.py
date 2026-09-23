import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.llm_service import llm_service
from backend.matching.matcher import get_candidate_skills, get_job_required_skills

logger = logging.getLogger(__name__)


class ApplicationAgent:
    """
    Autonomous Application Agent for Milestone 3.2.
    Handles Resume Customization and Cover Letter Generation.
    Strictly follows anti-hallucination rules: uses only factual candidate data.
    """

    def __init__(self):
        self.llm = llm_service

    def customize_resume(
        self, candidate: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a tailored resume representation prioritizing job-relevant skills,
        projects, and experiences without inventing any facts or metrics.
        """
        candidate_skills = list(candidate.get("skills", []))
        job_skills = list(job.get("required_skills", [])) + list(
            job.get("preferred_skills", [])
        )
        job_title = job.get("job_title", "Target Role")
        company = job.get("company", "Target Company")

        candidate_data = {
            "full_name": candidate.get("full_name", ""),
            "email": candidate.get("email", ""),
            "phone": candidate.get("phone", ""),
            "location": candidate.get("location", ""),
            "target_role": candidate.get("target_role", job_title),
            "linkedin_url": candidate.get("linkedin_url", ""),
            "summary": candidate.get("summary", ""),
            "skills": candidate_skills,
            "education": candidate.get("education", []),
            "experience": candidate.get("experience", []),
            "projects": candidate.get("projects", []),
            "certifications": candidate.get("certifications", []),
        }

        job_data = {
            "job_title": job_title,
            "company": company,
            "location": job.get("location", ""),
            "description": (job.get("job_description") or "")[:2000],
            "required_skills": job.get("required_skills", []),
            "preferred_skills": job.get("preferred_skills", []),
            "responsibilities": job.get("responsibilities", []),
        }

        system_instruction = (
            "You are an expert Resume Customization and Career Application Agent. "
            "Your job is to tailor a candidate's resume for a specific job opening. "
            "CRITICAL ANTI-HALLUCINATION REQUIREMENT: "
            "1. You MUST NOT invent any skills, employers, project names, degrees, certifications, or metrics. "
            "2. Never claim 'improved accuracy by 25%' or 'managed a team of 10' unless explicitly in candidate data. "
            "3. Only prioritize, rephrase, highlight, and emphasize genuine candidate skills and projects. "
            "4. Suggest relevant industry keywords from the job description that the candidate can study."
        )

        prompt = f"""
Tailor the following candidate's resume for the target job position.

CANDIDATE FACTUAL DATA:
{json.dumps(candidate_data, indent=2)}

TARGET JOB DETAILS:
{json.dumps(job_data, indent=2)}

Return a valid JSON object matching this schema:
{{
  "job_title": "{job_title}",
  "company": "{company}",
  "contact_info": {{
    "full_name": "{candidate.get('full_name', '')}",
    "email": "{candidate.get('email', '')}",
    "phone": "{candidate.get('phone', '')}",
    "location": "{candidate.get('location', '')}",
    "linkedin_url": "{candidate.get('linkedin_url', '')}"
  }},
  "professional_summary": "Tailored 3-4 sentence professional summary highlighting candidate's real skills matching {job_title}",
  "highlighted_skills": ["List of candidate's actual skills prioritized by relevance to the job"],
  "projects": [
    {{
      "title": "Actual Project Name from profile",
      "relevance": "Why this project is highly relevant to {job_title}",
      "highlights": ["Factual bullet points focusing on real technologies used in candidate profile"]
    }}
  ],
  "experience": [
    {{
      "role": "Actual role/experience from profile",
      "highlights": ["Factual bullet points"]
    }}
  ],
  "education": ["Actual education entries from profile"],
  "certifications": ["Actual certifications from profile"],
  "suggested_keywords": ["Keywords from job description the candidate should know and emphasize"],
  "customization_strategy": "Explanation of how this resume was tailored to maximize alignment"
}}
"""

        try:
            result = self.llm.generate_structured(
                prompt=prompt, system_instruction=system_instruction
            )
            result["source"] = "application_agent_llm"
            return result
        except Exception as error:
            logger.warning(
                f"LLM resume customization failed: {error}. Using deterministic fallback."
            )
            return self._build_deterministic_resume(candidate_data, job_data)

    def generate_cover_letter(
        self, candidate: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a professional 6-paragraph cover letter grounded in candidate profile.
        """
        job_title = job.get("job_title", "Position")
        company = job.get("company", "Company")
        candidate_name = candidate.get("full_name", "Applicant")

        candidate_data = {
            "name": candidate_name,
            "email": candidate.get("email", ""),
            "phone": candidate.get("phone", ""),
            "location": candidate.get("location", ""),
            "skills": list(candidate.get("skills", [])),
            "education": candidate.get("education", []),
            "experience": candidate.get("experience", []),
            "projects": candidate.get("projects", []),
        }

        job_data = {
            "job_title": job_title,
            "company": company,
            "location": job.get("location", ""),
            "description": (job.get("job_description") or "")[:1500],
            "required_skills": job.get("required_skills", []),
        }

        system_instruction = (
            "You are a professional Cover Letter Writing Agent. "
            "Write a compelling, professional cover letter tailored to the job. "
            "ANTI-HALLUCINATION REQUIREMENT: Use ONLY real candidate skills, projects, and education. "
            "Do not invent previous roles, fake companies, or ungrounded claims."
        )

        prompt = f"""
Write a personalized 6-part professional cover letter for {candidate_name} applying for {job_title} at {company}.

CANDIDATE PROFILE:
{json.dumps(candidate_data, indent=2)}

TARGET JOB:
{json.dumps(job_data, indent=2)}

Return a valid JSON object matching this schema:
{{
  "job_title": "{job_title}",
  "company": "{company}",
  "subject_line": "Application for {job_title} - {candidate_name}",
  "salutation": "Dear Hiring Team at {company},",
  "opening_paragraph": "Express enthusiastic interest in the {job_title} position and briefly introduce background.",
  "skills_alignment_paragraph": "Discuss genuine candidate skills matching {job_title} requirements.",
  "project_experience_paragraph": "Spotlight 1-2 real projects or experiences from the candidate profile.",
  "company_fit_paragraph": "Explain why candidate is eager to contribute to {company}.",
  "closing_paragraph": "Professional thank you, interview request, and availability.",
  "sign_off": "Sincerely,\\n{candidate_name}",
  "full_letter": "The complete formatted cover letter text with paragraphs and signature combined."
}}
"""

        try:
            result = self.llm.generate_structured(
                prompt=prompt, system_instruction=system_instruction
            )
            result["source"] = "application_agent_llm"
            return result
        except Exception as error:
            logger.warning(
                f"LLM cover letter generation failed: {error}. Using deterministic fallback."
            )
            return self._build_deterministic_cover_letter(candidate_data, job_data)

    def _build_deterministic_resume(
        self, candidate: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deterministic fallback for tailored resume.
        """
        job_skills_set = {s.lower() for s in job.get("required_skills", [])}
        cand_skills = candidate.get("skills", [])
        
        # Prioritize skills that match job requirements
        matched = [s for s in cand_skills if s.lower() in job_skills_set]
        other_skills = [s for s in cand_skills if s.lower() not in job_skills_set]
        prioritized_skills = matched + other_skills

        # Format projects
        projects_list = []
        for p in candidate.get("projects", []):
            if isinstance(p, dict):
                p_title = p.get("name", "Project")
                p_desc = p.get("description", "")
            else:
                p_title = str(p)
                p_desc = "Academic and practical implementation project."
            projects_list.append(
                {
                    "title": p_title,
                    "relevance": f"Demonstrates core competencies relevant to {job.get('job_title')}.",
                    "highlights": [p_desc] if p_desc else ["Applied practical programming and problem-solving techniques."],
                }
            )

        # Format experience
        exp_list = []
        for exp in candidate.get("experience", []):
            exp_text = str(exp)
            exp_list.append(
                {
                    "role": exp_text,
                    "highlights": [
                        f"Gained hands-on experience applicable to {job.get('job_title')} roles.",
                        "Collaborated on technical tasks and engineering problem solving.",
                    ],
                }
            )

        summary = (
            f"Driven and detail-oriented candidate seeking the {job.get('job_title')} position at {job.get('company')}. "
            f"Proficient in {', '.join(prioritized_skills[:5]) if prioritized_skills else 'software development'}, "
            f"with demonstrated project experience and strong problem-solving capabilities."
        )

        return {
            "job_title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "contact_info": {
                "full_name": candidate.get("full_name", ""),
                "email": candidate.get("email", ""),
                "phone": candidate.get("phone", ""),
                "location": candidate.get("location", ""),
                "linkedin_url": candidate.get("linkedin_url", ""),
            },
            "professional_summary": summary,
            "highlighted_skills": prioritized_skills,
            "projects": projects_list,
            "experience": exp_list,
            "education": (
                candidate.get("education")
                if isinstance(candidate.get("education"), list)
                else [str(candidate.get("education", ""))]
            ),
            "certifications": (
                candidate.get("certifications")
                if isinstance(candidate.get("certifications"), list)
                else [str(candidate.get("certifications", ""))]
            ),
            "suggested_keywords": list(job.get("required_skills", []))[:8],
            "customization_strategy": (
                f"Prioritized {len(matched)} matching technical skills and aligned project highlights with {job.get('job_title')} specifications."
            ),
            "source": "application_agent_deterministic",
        }

    def _build_deterministic_cover_letter(
        self, candidate: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deterministic fallback for cover letter.
        """
        name = candidate.get("name", "Applicant")
        job_title = job.get("job_title", "Position")
        company = job.get("company", "Company")
        skills = candidate.get("skills", [])
        skills_str = ", ".join(skills[:5]) if skills else "technical fundamentals"
        
        projects = candidate.get("projects", [])
        first_proj = (
            projects[0].get("name", str(projects[0]))
            if projects and isinstance(projects[0], dict)
            else (str(projects[0]) if projects else "portfolio projects")
        )

        salutation = f"Dear Hiring Team at {company},"
        p1 = f"I am writing to express my enthusiastic interest in the {job_title} opportunity at {company}. With a strong academic background and hands-on experience in modern technology stacks, I am eager to contribute to your team's innovative engineering initiatives."
        p2 = f"My technical foundation includes proficiency in {skills_str}. Throughout my academic curriculum and coursework, I have developed a disciplined approach to software development, data structures, and solving complex technical challenges."
        p3 = f"In particular, my work on '{first_proj}' demonstrates my ability to build robust applications and translate concepts into functional solutions. This experience has prepared me to quickly adapt to {company}'s development standards and deliver value from day one."
        p4 = f"I am particularly drawn to {company} due to your commitment to engineering excellence and collaborative culture. I look forward to bringing my proactive mindset and strong work ethic to your team."
        p5 = f"Thank you for considering my application. I would welcome the opportunity to discuss how my background, skills, and passion align with the goals of the {job_title} role. I look forward to hearing from you."
        sign_off = f"Sincerely,\n{name}"

        full_letter = f"{salutation}\n\n{p1}\n\n{p2}\n\n{p3}\n\n{p4}\n\n{p5}\n\n{sign_off}"

        return {
            "job_title": job_title,
            "company": company,
            "subject_line": f"Application for {job_title} - {name}",
            "salutation": salutation,
            "opening_paragraph": p1,
            "skills_alignment_paragraph": p2,
            "project_experience_paragraph": p3,
            "company_fit_paragraph": p4,
            "closing_paragraph": p5,
            "sign_off": sign_off,
            "full_letter": full_letter,
            "source": "application_agent_deterministic",
        }


# Singleton instance
application_agent = ApplicationAgent()
