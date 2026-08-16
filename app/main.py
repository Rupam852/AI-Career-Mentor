import os
import random
import pandas as pd
from fastapi import FastAPI, Request, File, UploadFile, Form, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List

from app.data_loader import data_loader
from app.ml_engine import ml_engine
from app.ai_service import ai_service
from app.parsers import extract_text_from_file, fetch_github_profile_data

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Career Mentor API", version="2.0.0")

# Enable CORS for frontend deployment (Vercel, Netlify, custom domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files
static_dir = os.path.join(os.path.dirname(__file__), 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    ml_engine.train_or_load_models()

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/options")
def get_options():
    return data_loader.get_unique_options()

# --- 1. Salary Prediction Endpoint ---
class SalaryRequest(BaseModel):
    industry: str
    job_title: str
    years_experience: float
    education_level: str
    degree_field: Optional[str] = "Computer Science"
    skills_count: Optional[int] = 5
    certifications_count: Optional[int] = 1
    company_size: Optional[str] = "Mid-size (201-1000)"
    work_type: Optional[str] = "Hybrid"

@app.post("/api/salary-prediction")
def predict_salary(req: SalaryRequest):
    return ml_engine.predict_salary(
        industry=req.industry,
        job_title=req.job_title,
        years_experience=req.years_experience,
        education_level=req.education_level,
        degree_field=req.degree_field,
        skills_count=req.skills_count,
        certifications_count=req.certifications_count,
        company_size=req.company_size,
        work_type=req.work_type
    )

# --- 2. Career Recommendation Endpoint ---
class CareerRequest(BaseModel):
    education_level: str
    years_experience: float
    work_style: str
    interests: str
    current_skills: str

@app.post("/api/career-recommendation")
def recommend_career(req: CareerRequest):
    return ml_engine.recommend_career(
        education_level=req.education_level,
        years_experience=req.years_experience,
        work_style=req.work_style,
        interests=req.interests,
        skills=req.current_skills
    )

# --- 3. Skill Gap Analysis Endpoint ---
class SkillGapRequest(BaseModel):
    current_role: str
    target_role: str
    current_skills: str

@app.post("/api/skill-gap")
def analyze_skill_gap(req: SkillGapRequest):
    df = data_loader.datasets.get('skill_gap')
    matched_row = None
    if df is not None:
        matches = df[df['target_role'].astype(str).str.lower().str.contains(req.target_role.lower(), na=False)]
        if not matches.empty:
            matched_row = matches.iloc[0]

    user_skills_list = [s.strip().lower() for s in req.current_skills.split(',') if s.strip()]

    if matched_row is not None:
        req_skills_str = str(matched_row.get('required_skills_for_target', ''))
        req_skills_list = [s.strip() for s in req_skills_str.split(',') if s.strip()]
        missing = [s for s in req_skills_list if s.lower() not in user_skills_list]
        gap_count = len(missing)
        readiness = round(max(10.0, 100.0 - (gap_count * 15.0)), 1)
        est_months = round(float(matched_row.get('estimated_months_to_close_gap', gap_count * 1.5)), 1)
        priority = str(matched_row.get('learning_priority', 'High' if gap_count > 3 else 'Medium'))
        resources = str(matched_row.get('recommended_resources', 'Online courses & hands-on projects'))
    else:
        req_skills_list = ["Advanced Domain Concepts", "System Design", "Cloud Infrastructure", "Project Management", "Leadership"]
        missing = [s for s in req_skills_list if s.lower() not in user_skills_list]
        gap_count = len(missing)
        readiness = round(max(20.0, 100.0 - (gap_count * 18.0)), 1)
        est_months = round(gap_count * 1.5, 1)
        priority = "High" if gap_count > 2 else "Medium"
        resources = "Coursera Specializations, Kaggle projects, Documentation"

    return {
        "current_role": req.current_role,
        "target_role": req.target_role,
        "user_skills": user_skills_list,
        "required_skills": req_skills_list,
        "missing_skills": missing,
        "skill_gap_count": gap_count,
        "readiness_percentage": readiness,
        "estimated_months_to_close_gap": est_months,
        "learning_priority": priority,
        "recommended_resources": resources
    }

# --- 4. Roadmap Generator Endpoint ---
class RoadmapRequest(BaseModel):
    current_role: str
    target_role: str
    weekly_hours: Optional[int] = 10
    api_key: Optional[str] = None

@app.post("/api/roadmap")
def generate_roadmap(req: RoadmapRequest):
    df = data_loader.datasets.get('roadmap')
    matched_row = None
    if df is not None:
        matches = df[df['target_role'].astype(str).str.lower().str.contains(req.target_role.lower(), na=False)]
        if not matches.empty:
            matched_row = matches.iloc[0]

    baseline = {}
    if matched_row is not None:
        baseline["total_months"] = int(matched_row.get('total_duration_months', 6))
        baseline["focus_skills"] = str(matched_row.get('focus_skills', 'Core Technical Skills'))
        baseline["target_certification"] = str(matched_row.get('target_certification', 'Certified Professional'))
        baseline["difficulty_level"] = str(matched_row.get('difficulty_level', 'Moderate'))
        baseline["steps_raw"] = str(matched_row.get('roadmap_steps', ''))
        baseline["milestones_raw"] = str(matched_row.get('milestones', ''))
    else:
        baseline["total_months"] = 6
        baseline["focus_skills"] = "Core Domain Skills, Project Execution, System Architecture"
        baseline["target_certification"] = "Professional Industry Certification"
        baseline["difficulty_level"] = "Moderate"
        baseline["steps_raw"] = "Phase 1 (1.5 mo): Fundamentals & Tooling | Phase 2 (1.5 mo): Core Mastery | Phase 3 (1.5 mo): Real Projects | Phase 4 (1.5 mo): Interview Prep"
        baseline["milestones_raw"] = "Month 2: Complete Core Concepts | Month 4: Portfolio Project Live | Month 6: Job Ready"

    # Call AI Model with Dataset Baseline
    if req.api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        ai_res = ai_service.generate_ai_roadmap(req.current_role, req.target_role, req.weekly_hours, baseline, req.api_key)
        if ai_res:
            ai_res["source"] = "Dataset + AI Career Architect"
            ai_res["current_role"] = req.current_role
            ai_res["target_role"] = req.target_role
            ai_res["weekly_hours"] = req.weekly_hours
            return ai_res

    # Fallback to Dataset Engine
    steps = [s.strip() for s in baseline["steps_raw"].split('|') if s.strip()]
    milestones = [m.strip() for m in baseline["milestones_raw"].split('|') if m.strip()]

    formatted_phases = []
    for idx, s in enumerate(steps):
        formatted_phases.append({
            "phase_name": f"Phase {idx+1}: {s.split(':')[0] if ':' in s else 'Module ' + str(idx+1)}",
            "description": s,
            "key_skills": [sk.strip() for sk in baseline["focus_skills"].split(',')[:4]],
            "recommended_resources": "Coursera, Udemy & Official Documentation",
            "project_idea": f"Build a hands-on portfolio project for {req.target_role}"
        })

    return {
        "source": "Dataset ML Baseline",
        "current_role": req.current_role,
        "target_role": req.target_role,
        "weekly_hours": req.weekly_hours,
        "total_duration_months": baseline["total_months"],
        "target_certification": baseline["target_certification"],
        "difficulty_level": baseline["difficulty_level"],
        "phases": formatted_phases,
        "milestones": milestones,
        "career_tips": "Dedicate consistent weekly study hours and build at least 2 public GitHub projects."
    }

# --- 5. Resume Analysis & PDF/DOCX Upload Endpoint ---
class ResumeRequest(BaseModel):
    resume_text: str
    target_job_title: Optional[str] = "Data Scientist"
    api_key: Optional[str] = None

@app.post("/api/resume-analysis")
def analyze_resume(req: ResumeRequest):
    # Check if Gemini AI evaluation is possible
    if req.api_key or os.environ.get("GEMINI_API_KEY"):
        ai_res = ai_service.evaluate_resume(req.resume_text, req.target_job_title, req.api_key)
        if ai_res:
            ai_res["source"] = "Gemini AI Engine"
            ai_res["word_count"] = len(req.resume_text.split())
            return ai_res

    # Local Dataset Fallback
    text = req.resume_text
    word_count = len(text.split())
    df = data_loader.datasets.get('resume')
    sample_row = df.iloc[0] if df is not None and not df.empty else None

    ats_score = min(96, max(35, int(45 + (min(word_count, 400) / 400.0) * 35 + (20 if "project" in text.lower() else 0))))
    keyword_match = min(92, max(30, int(ats_score * 0.9)))
    
    if sample_row is not None:
        strengths = str(sample_row.get('strengths', 'Strong hands-on experience and skills listed.'))
        weaknesses = str(sample_row.get('weaknesses', 'Could include more quantifiable metrics.'))
        suggestions = str(sample_row.get('improvement_suggestions', 'Add metrics (e.g. % growth, revenue impact).'))
    else:
        strengths = "Good technical clarity and readable format."
        weaknesses = "Lacks quantitative impact metrics."
        suggestions = "Quantify achievements (e.g., 'improved performance by 25%'); Add target keywords."

    rating = "Excellent" if ats_score >= 85 else ("Good" if ats_score >= 70 else "Average")

    return {
        "source": "Dataset ML Engine",
        "word_count": word_count,
        "ats_score": ats_score,
        "keyword_match_percentage": keyword_match,
        "overall_rating": rating,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_suggestions": suggestions
    }

@app.post("/api/resume-upload")
async def upload_resume(file: UploadFile = File(...), target_job_title: str = Form("Data Scientist"), api_key: Optional[str] = Form(None)):
    contents = await file.read()
    extracted_text = extract_text_from_file(contents, file.filename)
    
    if not extracted_text:
        return JSONResponse(status_code=400, content={"error": f"Could not extract text from file '{file.filename}'."})

    req = ResumeRequest(resume_text=extracted_text, target_job_title=target_job_title, api_key=api_key)
    res = analyze_resume(req)
    res["filename"] = file.filename
    res["extracted_preview"] = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
    return res

# --- 6. Interview Prep & Answer Evaluator ---
class InterviewRequest(BaseModel):
    job_title: str
    category: Optional[str] = "All Categories"
    industry: Optional[str] = "Information Technology"
    api_key: Optional[str] = None

@app.post("/api/interview-prep")
def get_interview_questions(req: InterviewRequest):
    # 1. Try OpenRouter AI Question Generator first
    if req.api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        prompt = f"""
        Generate a comprehensive 10-question interview question bank for the target job role: "{req.job_title}".
        Selected Category Filter: "{req.category}".

        Include a diverse mix of 10 real-world industry interview questions across:
        1. LeetCode DSA & Algorithm Coding Challenges
        2. System Design & Scalable Distributed Architecture
        3. Core Technical & Framework Deep Dives
        4. Behavioral STAR Method Leadership Scenarios

        Return a JSON response with exact key "questions" containing an array of 10 objects:
        [
          {{
            "question_id": 1,
            "question_type": "LeetCode Coding" or "System Design" or "Technical Deep Dive" or "Behavioral STAR",
            "difficulty_level": "Hard" or "Medium" or "Easy",
            "question_text": "Clear, detailed question text...",
            "key_evaluation_points": "Key concepts candidate should cover...",
            "ideal_answer_length_words": 150
          }}
        ]
        """
        ai_res = ai_service._call_openrouter_chain(prompt, req.api_key)
        if ai_res and isinstance(ai_res.get("questions"), list) and len(ai_res["questions"]) > 0:
            return {"job_title": req.job_title, "category": req.category, "questions": ai_res["questions"]}

    # 2. Dataset + Baseline Question Engine Fallback
    df = data_loader.datasets.get('interview')
    questions = []
    if df is not None and not df.empty:
        matches = df[df['job_title'].astype(str).str.lower().str.contains(req.job_title.lower(), na=False)]
        if matches.empty:
            matches = df.sample(min(8, len(df)))
        else:
            matches = matches.head(8)

        for idx, row in matches.iterrows():
            questions.append({
                "question_id": len(questions) + 1,
                "question_type": str(row.get('question_type', 'Technical')),
                "difficulty_level": str(row.get('difficulty_level', 'Medium')),
                "question_text": str(row.get('question_text', '')),
                "key_evaluation_points": str(row.get('key_evaluation_points', 'Core domain concepts and problem-solving approach.')),
                "ideal_answer_length_words": int(row.get('ideal_answer_length_words', 120))
            })

    # Supplementary LeetCode / System Design fallback questions if fewer than 8
    supplementary = [
        {
            "question_id": len(questions) + 1,
            "question_type": "LeetCode Coding",
            "difficulty_level": "Medium",
            "question_text": f"How would you optimize time and space complexity for a data processing pipeline in {req.job_title}?",
            "key_evaluation_points": "Big-O time complexity, space trade-offs, caching, vectorization.",
            "ideal_answer_length_words": 120
        },
        {
            "question_id": len(questions) + 2,
            "question_type": "System Design",
            "difficulty_level": "Hard",
            "question_text": f"Design a high-throughput, low-latency microservice architecture for {req.job_title} tasks.",
            "key_evaluation_points": "Load balancing, database sharding, caching, API gateways, fault tolerance.",
            "ideal_answer_length_words": 150
        },
        {
            "question_id": len(questions) + 3,
            "question_type": "Behavioral STAR",
            "difficulty_level": "Medium",
            "question_text": "Describe a critical production bug or system failure you resolved under tight deadline pressures.",
            "key_evaluation_points": "STAR framework (Situation, Task, Action, Result), root cause analysis, resilience.",
            "ideal_answer_length_words": 130
        }
    ]

    for q in supplementary:
        if len(questions) < 10:
            questions.append(q)

    return {"job_title": req.job_title, "category": req.category, "questions": questions}

class AnswerEvaluationRequest(BaseModel):
    job_title: str
    question_text: str
    candidate_answer: str
    api_key: Optional[str] = None

@app.post("/api/interview-evaluate")
def evaluate_interview_answer(req: AnswerEvaluationRequest):
    # Check Gemini AI First
    if req.api_key or os.environ.get("GEMINI_API_KEY"):
        ai_res = ai_service.evaluate_interview_answer(req.question_text, req.candidate_answer, req.job_title, req.api_key)
        if ai_res:
            ai_res["source"] = "Gemini AI Engine"
            return ai_res

    # Rule-Based / Dataset Fallback
    word_count = len(req.candidate_answer.split())
    score = min(9.5, max(4.0, round(5.0 + (word_count / 120.0) * 4.0, 1)))
    tier = "Solid Response" if score >= 7.5 else ("Needs Improvement" if score < 6.0 else "Average Response")
    
    return {
        "source": "Dataset Rule Engine",
        "score_out_of_10": score,
        "performance_tier": tier,
        "strengths": "Good effort providing structured thoughts in response.",
        "missing_key_points": "Could expand more on specific technical trade-offs, metrics, or methodology.",
        "constructive_feedback": "Use the STAR method (Situation, Task, Action, Result) to structure your response clearly.",
        "ideal_model_answer": "Focus on state-of-the-art methodology, explain design trade-offs step-by-step, and state quantitative impact metrics."
    }

# --- 7. Live GitHub API & Review Endpoint ---
class GitHubLiveRequest(BaseModel):
    username_or_url: str
    api_key: Optional[str] = None

@app.post("/api/github-live-review")
def review_github_live(req: GitHubLiveRequest):
    gh_data = fetch_github_profile_data(req.username_or_url)
    if "error" in gh_data:
        return JSONResponse(status_code=400, content=gh_data)

    # Check OpenRouter / Gemini AI Audit
    if req.api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        ai_res = ai_service.review_github_profile(gh_data, req.api_key)
        if ai_res:
            ai_res["source"] = "Live GitHub API + AI Code Architect"
            ai_res["raw_metrics"] = gh_data
            return ai_res

    # Query local dataset for reference baseline
    df = data_loader.datasets.get('github')
    sample_row = df.iloc[0] if df is not None and not df.empty else None

    repos = gh_data.get('public_repos', 0)
    stars = gh_data.get('total_stars', 0)
    followers = gh_data.get('followers', 0)
    top_langs = gh_data.get('top_languages', [])

    score = min(99, max(35, int(35 + min(repos, 30) * 1.5 + min(stars, 50) * 0.8 + min(followers, 50) * 0.6)))
    tier = "Senior Open-Source Engineer" if score >= 85 else ("Solid Active Developer" if score >= 65 else "Building Portfolio")
    grade = "A+" if score >= 90 else ("A" if score >= 75 else ("B+" if score >= 60 else "B"))

    strengths = f"Active GitHub contributor with {repos} public repositories, {stars} total stars, and {followers} followers. Dominant languages: {', '.join(top_langs[:3]) if top_langs else 'Software Engineering'}."
    weaknesses = str(sample_row.get('weaknesses', 'Could add more detailed README documentation and release tags to top repositories.')) if sample_row is not None else "Add detailed README documentation."
    tips = str(sample_row.get('improvement_suggestions', 'Pin top 4 projects, attach live web app demo URLs, and write clear commit logs.')) if sample_row is not None else "Pin top projects with demo links."

    return {
        "source": "Live GitHub API + Dataset Rules",
        "raw_metrics": gh_data,
        "developer_score": score,
        "developer_tier": tier,
        "code_quality_grade": grade,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_suggestions": tips,
        "top_technologies": top_langs if top_langs else ["Git", "Software Development"]
    }

# --- 8. LinkedIn Review Endpoint ---
class LinkedInRequest(BaseModel):
    linkedin_url: str
    headline: Optional[str] = "Professional"
    summary_text: Optional[str] = ""
    certifications: Optional[str] = ""
    featured_projects: Optional[str] = ""
    post_activity: Optional[str] = "Active"
    api_key: Optional[str] = None

@app.post("/api/linkedin-review")
def review_linkedin(req: LinkedInRequest):
    clean_handle = req.linkedin_url.strip().rstrip('/')
    if 'linkedin.com/in/' in clean_handle:
        clean_handle = clean_handle.split('linkedin.com/in/')[-1].split('/')[0]

    summary_words = len(req.summary_text.split()) if req.summary_text and req.summary_text.strip() else 0
    headline_text = req.headline.strip() if req.headline and req.headline.strip() else "Professional Member"
    certs_text = req.certifications.strip() if req.certifications and req.certifications.strip() else "None provided"
    projects_text = req.featured_projects.strip() if req.featured_projects and req.featured_projects.strip() else "None provided"
    activity_level = req.post_activity.strip() if req.post_activity and req.post_activity.strip() else "Active Member"

    # Query dataset baseline
    df = data_loader.datasets.get('linkedin')
    sample_row = df.iloc[0] if df is not None and not df.empty else None

    # Check AI LLM Audit
    if req.api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        prompt = f"""
        Audit the following Comprehensive LinkedIn Profile:
        - Profile Handle/URL: {clean_handle or req.linkedin_url}
        - Headline: "{headline_text}"
        - Summary/Bio Text ({summary_words} words): "{req.summary_text}"
        - Certifications & Licenses: "{certs_text}"
        - Featured Projects & Links: "{projects_text}"
        - Post Activity & Engagement Level: "{activity_level}"

        Provide a JSON response with exact keys:
        - "profile_completeness_score": Integer (0-100)
        - "review_rating": String ("All-Star Profile", "Intermediate Profile", "Needs Growth")
        - "strengths": String highlighting profile strengths (headline quality, certifications, featured projects, activity)
        - "weaknesses": String highlighting major profile gaps (summary depth, missing certs/projects, engagement)
        - "improvement_suggestions": String with 3 actionable recommendations to attract top recruiters
        """
        ai_res = ai_service._call_openrouter_chain(prompt, req.api_key)
        if ai_res:
            score = ai_res.get("profile_completeness_score") or ai_res.get("profile_score") or ai_res.get("score") or 85
            rating = ai_res.get("review_rating") or ai_res.get("rating") or "All-Star Profile"
            strengths = ai_res.get("strengths") or "Strong professional headline, solid project positioning, and clear certifications."
            weaknesses = ai_res.get("weaknesses") or "Consider expanding featured projects and posting weekly technical insights."
            tips = ai_res.get("improvement_suggestions") or ai_res.get("tips") or "Add top 10+ industry skills, showcase live project links, and request recommendations."

            return {
                "source": "AI Profile Auditor (" + str(ai_res.get("ai_model_used", "OpenRouter AI")) + ")",
                "linkedin_handle": clean_handle or "LinkedIn Member",
                "headline_analyzed": headline_text,
                "summary_words_count": summary_words,
                "certifications_analyzed": certs_text,
                "projects_analyzed": projects_text,
                "activity_level": activity_level,
                "profile_completeness_score": score,
                "review_rating": rating,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "improvement_suggestions": tips
            }

    # Local Dataset Fallback
    bonus = (10 if certs_text != "None provided" else 0) + (10 if projects_text != "None provided" else 0)
    score = min(98, max(40, int(40 + (min(len(headline_text), 40) / 40.0) * 20 + (min(summary_words, 100) / 100.0) * 20 + bonus)))
    rating = "All-Star Profile" if score >= 80 else ("Intermediate Profile" if score >= 60 else "Needs Growth")

    strengths = str(sample_row.get('strengths', 'Good headline structure and professional positioning.')) if sample_row is not None else "Good headline structure."
    weaknesses = str(sample_row.get('weaknesses', 'Add a 3-5 sentence summary and request recommendations.')) if sample_row is not None else "Summary could be expanded."
    tips = str(sample_row.get('improvement_suggestions', 'Write a clear About section and add top technical skills.')) if sample_row is not None else "Add industry skills."

    return {
        "source": "Dataset Profile Auditor",
        "linkedin_handle": clean_handle or "LinkedIn Member",
        "headline_analyzed": headline_text,
        "summary_words_count": summary_words,
        "certifications_analyzed": certs_text,
        "projects_analyzed": projects_text,
        "activity_level": activity_level,
        "profile_completeness_score": score,
        "review_rating": rating,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_suggestions": tips
    }
