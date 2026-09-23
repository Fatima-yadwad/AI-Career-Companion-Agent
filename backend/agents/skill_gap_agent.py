import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.llm_service import llm_service
from backend.matching.matcher import (
    calculate_skill_match,
    get_candidate_skills,
    get_job_preferred_skills,
    get_job_required_skills,
    normalize_skill,
)

logger = logging.getLogger(__name__)


class SkillGapAgent:
    """
    Autonomous Skill Gap Analysis Agent for Milestone 3.1.
    Performs comprehensive, multi-dimensional gap analysis between a student's
    actual structured profile and a target job. Strictly avoids hallucination.
    """

    def __init__(self):
        self.llm = llm_service

    def analyze_skill_gap(
        self, candidate: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs complete skill gap analysis comparing candidate against selected job.
        Returns structured results containing matches, critical gaps, partial gaps,
        preferred gaps, experience/qualification gaps, and actionable recommendations.
        """
        # Extract normalized candidate and job data
        candidate_skills = get_candidate_skills(candidate)
        required_skills = get_job_required_skills(job)
        preferred_skills = get_job_preferred_skills(job)

        # Deterministic foundation
        req_match = calculate_skill_match(candidate_skills, required_skills)
        pref_match = calculate_skill_match(candidate_skills, preferred_skills)

        matched_req = req_match.get("matched", [])
        missing_req = req_match.get("missing", [])
        matched_pref = pref_match.get("matched", [])
        missing_pref = pref_match.get("missing", [])

        # Total score calculation
        total_unique_skills = len(required_skills | preferred_skills)
        matched_count = len(matched_req) + len(matched_pref)
        match_percentage = (
            round((matched_count / total_unique_skills) * 100, 2)
            if total_unique_skills > 0
            else 100.0
        )

        # Prepare evidence packet for LLM
        candidate_evidence = {
            "name": candidate.get("full_name", "Student"),
            "target_role": candidate.get("target_role", ""),
            "skills": list(candidate.get("skills", [])),
            "education": candidate.get("education", []),
            "experience": candidate.get("experience", []),
            "projects": candidate.get("projects", []),
            "certifications": candidate.get("certifications", []),
        }

        job_evidence = {
            "job_id": job.get("job_id", ""),
            "job_title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "work_type": job.get("work_type", ""),
            "description": (job.get("job_description") or "")[:2000],
            "required_skills": list(job.get("required_skills", [])),
            "preferred_skills": list(job.get("preferred_skills", [])),
            "qualifications": list(job.get("qualifications", [])),
            "responsibilities": list(job.get("responsibilities", [])),
            "experience_requirements": job.get("experience_requirements", ""),
            "education_requirements": job.get("education_requirements", ""),
        }

        system_instruction = (
            "You are an expert AI Career and Skill Gap Advisor. "
            "You analyze the gap between a candidate's verified profile and a target job. "
            "CRITICAL ANTI-HALLUCINATION RULE: Use ONLY the provided candidate facts and job requirements. "
            "NEVER invent skills, projects, achievements, or experience the candidate does not have. "
            "If evidence is absent, state: 'No evidence found in profile'. "
            "Distinguish strictly between Required Skills and Preferred Skills. "
            "Provide realistic, highly actionable recommendations for closing critical gaps."
        )

        prompt = f"""
Perform a structured Skill Gap Analysis for the following candidate applying for the target job.

CANDIDATE PROFILE:
{json.dumps(candidate_evidence, indent=2)}

TARGET JOB REQUIREMENTS:
{json.dumps(job_evidence, indent=2)}

DETERMINISTIC SKILL ANALYSIS:
- Matched Required Skills: {matched_req}
- Missing Required Skills: {missing_req}
- Matched Preferred Skills: {matched_pref}
- Missing Preferred Skills: {missing_pref}

Return ONLY a valid JSON object with the following schema:
{{
  "job_title": "{job.get('job_title', '')}",
  "company": "{job.get('company', '')}",
  "summary": "2-3 sentence overview of the candidate's alignment and primary gaps",
  "strong_matches": [
    {{
      "skill": "skill name",
      "category": "Required Skill | Preferred Skill | Core Competency",
      "current_evidence": "Exact evidence from candidate profile/projects/education",
      "alignment_note": "Why this fulfills the role requirement"
    }}
  ],
  "critical_gaps": [
    {{
      "skill": "missing required skill name",
      "category": "Missing Required Skill",
      "importance": "High",
      "why_it_matters": "Context on how this is used in the role",
      "current_evidence": "No evidence found in profile",
      "recommended_action": "Concrete hands-on project or tutorial to build this skill"
    }}
  ],
  "partial_gaps": [
    {{
      "skill": "partially matched skill or related tool",
      "category": "Partial Skill Match",
      "importance": "Medium",
      "why_it_matters": "Why upgrading from candidate's current related skill to this target is needed",
      "current_evidence": "Related skill found in candidate profile",
      "recommended_action": "Targeted bridging project or framework translation step"
    }}
  ],
  "preferred_gaps": [
    {{
      "skill": "preferred skill name",
      "category": "Missing Preferred Skill",
      "importance": "Medium | Low",
      "why_it_matters": "How having this provides a competitive advantage",
      "current_evidence": "No evidence found in profile",
      "recommended_action": "Suggested exploratory learning resource or micro-project"
    }}
  ],
  "experience_gaps": [
    {{
      "requirement": "job experience requirement",
      "candidate_status": "candidate's actual background summary",
      "impact": "Low | Moderate | High",
      "mitigation_strategy": "How to compensate using projects, open-source, or portfolio"
    }}
  ],
  "qualification_gaps": [
    {{
      "requirement": "degree/education requirement",
      "candidate_status": "candidate's actual education",
      "is_met": true
    }}
  ],
  "recommendations": [
    {{
      "priority": 1,
      "title": "Title of action item",
      "skill_target": "Skill addressed",
      "description": "Step-by-step actionable advice",
      "estimated_time": "e.g., 1-2 weeks",
      "deliverable": "Specific project deliverable or portfolio addition"
    }}
  ]
}}
"""

        try:
            llm_result = self.llm.generate_structured(
                prompt=prompt, system_instruction=system_instruction
            )
            # Ensure top-level fields
            llm_result["job_title"] = job.get("job_title", "")
            llm_result["company"] = job.get("company", "")
            llm_result["skill_match_percentage"] = match_percentage
            llm_result["matched_skills"] = sorted(
                list(set(matched_req) | set(matched_pref))
            )
            llm_result["missing_skills"] = sorted(
                list(set(missing_req) | set(missing_pref))
            )
            llm_result["source"] = "skill_gap_agent_llm"
            return llm_result

        except Exception as error:
            logger.warning(
                f"LLM skill gap generation failed: {error}. Using deterministic fallback."
            )
            return self._build_deterministic_fallback(
                candidate=candidate,
                job=job,
                matched_req=matched_req,
                missing_req=missing_req,
                matched_pref=matched_pref,
                missing_pref=missing_pref,
                match_percentage=match_percentage,
            )

    def _build_deterministic_fallback(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        matched_req: List[str],
        missing_req: List[str],
        matched_pref: List[str],
        missing_pref: List[str],
        match_percentage: float,
    ) -> Dict[str, Any]:
        """
        Deterministic, robust fallback when LLM is offline or rate-limited.
        """
        strong_matches = [
            {
                "skill": s,
                "category": "Required Skill",
                "current_evidence": f"Found in profile skills: {s}",
                "alignment_note": f"Directly satisfies the {job.get('job_title', 'role')} requirement.",
            }
            for s in matched_req
        ] + [
            {
                "skill": s,
                "category": "Preferred Skill",
                "current_evidence": f"Found in profile skills: {s}",
                "alignment_note": "Fulfills a preferred qualification for the role.",
            }
            for s in matched_pref
        ]

        critical_gaps = [
            {
                "skill": s,
                "category": "Missing Required Skill",
                "importance": "High",
                "why_it_matters": f"Essential core competency required for {job.get('job_title', 'this role')}.",
                "current_evidence": "No evidence found in profile",
                "recommended_action": f"Build a practical hands-on project implementing {s} and publish to GitHub.",
            }
            for s in missing_req
        ]

        preferred_gaps = [
            {
                "skill": s,
                "category": "Missing Preferred Skill",
                "importance": "Medium",
                "why_it_matters": f"Bonus skill that gives an edge for {job.get('company', 'this company')}.",
                "current_evidence": "No evidence found in profile",
                "recommended_action": f"Explore {s} fundamentals through tutorials and small utility scripts.",
            }
            for s in missing_pref
        ]

        recommendations = []
        for i, skill in enumerate(missing_req[:3], start=1):
            recommendations.append(
                {
                    "priority": i,
                    "title": f"Master {skill} with a portfolio project",
                    "skill_target": skill,
                    "description": f"Design and deploy a working application utilizing {skill} to showcase on your resume.",
                    "estimated_time": "1-2 weeks",
                    "deliverable": f"GitHub repository and live demo demonstrating {skill}.",
                }
            )

        return {
            "job_title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "summary": (
                f"Candidate matches {len(matched_req)} required skills and has "
                f"{len(missing_req)} critical skill gaps for the {job.get('job_title', 'target')} role."
            ),
            "strong_matches": strong_matches,
            "critical_gaps": critical_gaps,
            "partial_gaps": [],
            "preferred_gaps": preferred_gaps,
            "experience_gaps": [
                {
                    "requirement": str(job.get("experience_requirements", "0-1 years / Fresher")),
                    "candidate_status": "Academic and project experience",
                    "impact": "Low",
                    "mitigation_strategy": "Highlight strong domain projects and technical proficiency in interview.",
                }
            ],
            "qualification_gaps": [
                {
                    "requirement": str(job.get("education_requirements", "Bachelor's degree")),
                    "candidate_status": str(candidate.get("education", "Undergraduate")),
                    "is_met": True,
                }
            ],
            "recommendations": recommendations,
            "skill_match_percentage": match_percentage,
            "matched_skills": sorted(list(set(matched_req) | set(matched_pref))),
            "missing_skills": sorted(list(set(missing_req) | set(missing_pref))),
            "source": "skill_gap_agent_deterministic",
        }


# Singleton instance
skill_gap_agent = SkillGapAgent()
