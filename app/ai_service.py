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

ai_service = AIService()
