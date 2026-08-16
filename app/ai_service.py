import os
import json
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
    "openai/gpt-4o-mini",
    "qwen/qwen-2.5-coder-32b-instruct",
    "meta-llama/llama-3.1-8b-instruct"
]

class AIService:
    def __init__(self):
        self.default_api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""

    def _call_openrouter_chain(self, prompt: str, provided_key: str = None):
        key = provided_key.strip() if provided_key and provided_key.strip() else self.default_api_key
        if not key:
            return None

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-career-mentor.vercel.app",
            "X-Title": "AI Career Mentor"
        }

        # Try fallback chain model by model
        for model in FALLBACK_MODELS:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an expert AI Career Coach. Always output valid raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            try:
                res = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data['choices'][0]['message']['content']
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)
                    parsed["ai_model_used"] = model
                    return parsed
                else:
                    print(f"Model '{model}' status {res.status_code}: {res.text[:100]}")
            except Exception as e:
                print(f"Model '{model}' exception:", e)
                continue

        return None

    def evaluate_resume(self, resume_text: str, target_job_title: str, api_key: str = None):
        prompt = f"""
        Analyze the following resume for the target job role: '{target_job_title}'.

        Resume Text:
        \"\"\"{resume_text[:3500]}\"\"\"

        Provide a JSON response with exact keys:
        - "ats_score": Integer (0-100)
        - "overall_rating": String ("Needs Improvement", "Average", "Good", "Outstanding")
        - "strengths": String with 2-3 key strengths
        - "weaknesses": String with 2-3 major weaknesses
        - "missing_keywords": List of 3-5 missing technical keywords
        - "improvement_suggestions": String with actionable ATS improvement steps
        """
        return self._call_openrouter_chain(prompt, api_key)

    def evaluate_interview_answer(self, question_text: str, candidate_answer: str, job_title: str, api_key: str = None):
        prompt = f"""
        You are a Senior Technical Interviewer evaluating a candidate for a '{job_title}' position.
        
        Question: "{question_text}"
        Candidate's Written Answer: "{candidate_answer}"

        Evaluate the response and provide a JSON with exact keys:
        - "score_out_of_10": Float (1.0 to 10.0)
        - "performance_tier": String ("Needs Improvement", "Solid Response", "Exceptional Answer")
        - "strengths": String explaining what candidate did well
        - "missing_key_points": String detailing technical or behavioral points missing
        - "constructive_feedback": String giving specific advice on how to improve this answer
        - "ideal_model_answer": String giving an exemplary 3-4 sentence response for this question
        """
        return self._call_openrouter_chain(prompt, api_key)

    def review_github_profile(self, github_data: dict, api_key: str = None):
        prompt = f"""
        You are a Technical Recruiter auditing a software engineer's GitHub profile.
        
        GitHub Profile Data:
        {json.dumps(github_data, indent=2)}

        Provide a JSON response with exact keys:
        - "profile_score": Integer (0-100)
        - "review_rating": String ("Foundational", "Active Contributor", "Outstanding Developer")
        - "strengths": String highlighting repository quality or activity
        - "weaknesses": String pointing out profile gaps
        - "improvement_suggestions": String with 2-3 actionable recommendations
        """
        return self._call_openrouter_chain(prompt, api_key)

    def generate_ai_roadmap(self, current_role: str, target_role: str, weekly_hours: int, dataset_baseline: dict = None, api_key: str = None):
        prompt = f"""
        You are a Principal Career Architect and Tech Mentor. Generate a highly comprehensive, step-by-step learning and career transition roadmap.

        Candidate Transition:
        - Current Role: "{current_role}"
        - Target Goal Role: "{target_role}"
        - Weekly Commitment: {weekly_hours} hours/week
        - Baseline Industry Focus: "{dataset_baseline.get('focus_skills', 'Core Technical Skills') if dataset_baseline else 'Technical Skills'}"

        Provide a JSON response with exact keys:
        - "total_duration_months": Integer (calculated based on transition gap & weekly hours)
        - "target_certification": String (Top recognized industry certification)
        - "difficulty_level": String ("Beginner Friendly", "Moderate", "Challenging / Advanced")
        - "phases": List of 4 distinct Phase objects, each having:
            - "phase_name": String (e.g. "Phase 1: Fundamentals & Tooling (Months 1-2)")
            - "description": String (High level goal of this phase)
            - "key_skills": List of strings (4-5 skills)
            - "recommended_resources": String (Specific top courses, books, documentation)
            - "project_idea": String (Specific portfolio project to build during this phase)
        - "milestones": List of 3-4 milestone strings (e.g. "Month 2: Complete Core Python & SQL Portfolio Project")
        - "career_tips": String (2-3 expert tips to crack interviews for this target role)
        """
        return self._call_openrouter_chain(prompt, api_key)

ai_service = AIService()
