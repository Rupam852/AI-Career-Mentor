import os
import json
from google import genai
from google.genai import types

class AIService:
    def __init__(self):
        self.default_api_key = os.environ.get("GEMINI_API_KEY", "")

    def get_client(self, provided_key: str = None):
        key = provided_key.strip() if provided_key and provided_key.strip() else self.default_api_key
        if key:
            try:
                return genai.Client(api_key=key)
            except Exception as e:
                print("Failed to initialize Gemini client:", e)
        return None

    def evaluate_resume(self, resume_text: str, target_job_title: str, api_key: str = None):
        client = self.get_client(api_key)
        if not client:
            return None # Signal fallback to dataset engine

        prompt = f"""
        You are an expert HR Specialist and ATS Resume Screener. Analyze the following resume for the target job role: '{target_job_title}'.

        Resume Text:
        \"\"\"{resume_text[:4000]}\"\"\"

        Provide a JSON object response with the following exact keys:
        - "ats_score": Integer between 0 and 100
        - "overall_rating": String ("Needs Improvement", "Average", "Good", "Outstanding")
        - "strengths": String detailing 2-3 key strengths
        - "weaknesses": String detailing 2-3 major weaknesses
        - "missing_keywords": List of 3-5 missing technical keywords
        - "improvement_suggestions": String with actionable steps to boost ATS match
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print("Gemini API Resume evaluation error:", e)
            return None

    def evaluate_interview_answer(self, question_text: str, candidate_answer: str, job_title: str, api_key: str = None):
        client = self.get_client(api_key)
        if not client:
            return None # Signal fallback

        prompt = f"""
        You are a Senior Technical Interviewer for a '{job_title}' position.
        
        Question: "{question_text}"
        Candidate's Answer: "{candidate_answer}"

        Evaluate the candidate's answer thoroughly and provide a JSON response with exact keys:
        - "score_out_of_10": Float between 1.0 and 10.0
        - "performance_tier": String ("Needs Improvement", "Solid Response", "Exceptional Answer")
        - "strengths": String explaining what the candidate did well
        - "missing_key_points": String detailing technical or behavioral points missing from their answer
        - "constructive_feedback": String providing specific advice on how to improve this answer
        - "ideal_model_answer": String giving an exemplary 3-4 sentence response for this question
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print("Gemini API Interview evaluation error:", e)
            return None

    def review_github_profile(self, github_data: dict, api_key: str = None):
        client = self.get_client(api_key)
        if not client:
            return None

        prompt = f"""
        You are a Developer Relations & Technical Recruiter auditing a software engineer's GitHub profile.
        
        GitHub Profile Data:
        {json.dumps(github_data, indent=2)}

        Provide a JSON response with exact keys:
        - "profile_score": Integer between 0 and 100
        - "review_rating": String ("Foundational", "Active Contributor", "Outstanding Developer")
        - "strengths": String highlighting repository quality or activity
        - "weaknesses": String pointing out profile gaps
        - "improvement_suggestions": String with 2-3 actionable recommendations to build credibility
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print("Gemini API GitHub review error:", e)
            return None

ai_service = AIService()
