import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from app.data_loader import data_loader

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
os.makedirs(MODEL_DIR, exist_ok=True)

class MLEngine:
    def __init__(self):
        self.salary_model_path = os.path.join(MODEL_DIR, 'salary_model.joblib')
        self.career_vectorizer_path = os.path.join(MODEL_DIR, 'career_vectorizer.joblib')
        self.career_matrix_path = os.path.join(MODEL_DIR, 'career_matrix.joblib')
        self.salary_model = None
        self.career_vectorizer = None
        self.career_matrix = None
        self.career_df = None
        
    def train_or_load_models(self):
        # 1. Train or Load Salary Prediction Model
        if os.path.exists(self.salary_model_path):
            try:
                self.salary_model = joblib.load(self.salary_model_path)
                print("Loaded pre-trained Salary Model.")
            except Exception as e:
                print("Failed to load salary model, retraining...", e)
                self._train_salary_model()
        else:
            self._train_salary_model()

        # 2. Train or Load Career Recommendation Engine
        if os.path.exists(self.career_vectorizer_path) and os.path.exists(self.career_matrix_path):
            try:
                self.career_vectorizer = joblib.load(self.career_vectorizer_path)
                self.career_matrix = joblib.load(self.career_matrix_path)
                self.career_df = data_loader.datasets.get('career')
                print("Loaded pre-trained Career Recommendation Engine.")
            except Exception as e:
                print("Failed to load career model, retraining...", e)
                self._train_career_engine()
        else:
            self._train_career_engine()

    def _train_salary_model(self):
        print("Training Salary Prediction Model...")
        df = data_loader.datasets.get('salary')
        if df is None or df.empty:
            print("Salary dataset missing!")
            return

        # Prepare features & target
        features = ['industry', 'job_title', 'years_experience', 'education_level', 
                    'degree_field', 'skills_count', 'certifications_count', 'company_size', 'work_type']
        target = 'predicted_salary_usd'

        # Drop rows with missing critical values
        df_clean = df.dropna(subset=features + [target]).copy()
        
        cat_features = ['industry', 'job_title', 'education_level', 'degree_field', 'company_size', 'work_type']
        num_features = ['years_experience', 'skills_count', 'certifications_count']

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), num_features),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features)
            ]
        )

        # Build Pipeline with Random Forest Regressor
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', RandomForestRegressor(n_estimators=50, max_depth=15, random_state=42, n_jobs=-1))
        ])

        X = df_clean[features]
        y = df_clean[target]

        # Train on a sample (up to 30,000) for fast training speed & accuracy balance
        if len(X) > 30000:
            X_sample, _, y_sample, _ = train_test_split(X, y, train_size=30000, random_state=42)
        else:
            X_sample, y_sample = X, y

        pipeline.fit(X_sample, y_sample)
        joblib.dump(pipeline, self.salary_model_path)
        self.salary_model = pipeline
        print("Salary Model trained and saved successfully.")

    def _train_career_engine(self):
        print("Building AI Career Recommendation Index...")
        df = data_loader.datasets.get('career')
        if df is None or df.empty:
            print("Career dataset missing!")
            return

        self.career_df = df.copy()
        # Combine relevant text columns into a feature representation
        df_text = df['interests'].fillna('') + ' ' + df['current_skills'].fillna('') + ' ' + df['work_style'].fillna('') + ' ' + df['education_level'].fillna('')
        
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        matrix = vectorizer.fit_transform(df_text)

        joblib.dump(vectorizer, self.career_vectorizer_path)
        joblib.dump(matrix, self.career_matrix_path)

        self.career_vectorizer = vectorizer
        self.career_matrix = matrix
        print("Career Recommendation Index built and saved successfully.")

    def predict_salary(self, industry, job_title, years_experience, education_level, degree_field="Computer Science", skills_count=5, certifications_count=1, company_size="Mid-size (201-1000)", work_type="Hybrid"):
        if self.salary_model is None:
            return {"error": "Salary model not trained"}

        input_data = pd.DataFrame([{
            'industry': industry,
            'job_title': job_title,
            'years_experience': float(years_experience),
            'education_level': education_level,
            'degree_field': degree_field,
            'skills_count': int(skills_count),
            'certifications_count': int(certifications_count),
            'company_size': company_size,
            'work_type': work_type
        }])

        predicted_val = self.salary_model.predict(input_data)[0]
        min_salary = round(predicted_val * 0.88, -2)
        max_salary = round(predicted_val * 1.12, -2)
        estimated = round(predicted_val, -2)

        # Convert to Indian Rupees (INR) - 1 USD = 83.5 INR
        usd_to_inr = 83.5
        estimated_inr = round(estimated * usd_to_inr)
        min_inr = round(min_salary * usd_to_inr)
        max_inr = round(max_salary * usd_to_inr)

        def format_inr(val):
            if val >= 10000000:
                return f"₹{val/10000000:.2f} Cr"
            elif val >= 100000:
                return f"₹{val/100000:.2f} Lakhs"
            else:
                return f"₹{val:,.0f}"

        formatted_inr_main = format_inr(estimated_inr)
        formatted_inr_range = f"{format_inr(min_inr)} - {format_inr(max_inr)}"

        return {
            "predicted_salary_usd": estimated,
            "min_salary_usd": min_salary,
            "max_salary_usd": max_salary,
            "predicted_salary_inr": estimated_inr,
            "min_salary_inr": min_inr,
            "max_salary_inr": max_inr,
            "formatted_salary_inr": f"{formatted_inr_main} / year",
            "formatted_salary_usd": f"${estimated:,.0f} / year",
            "range_inr": formatted_inr_range,
            "range_usd": f"${min_salary:,.0f} - ${max_salary:,.0f}",
            "formatted_salary": f"{formatted_inr_main} (${estimated:,.0f} USD) / year",
            "range": f"{formatted_inr_range} (${min_salary:,.0f} - ${max_salary:,.0f} USD)"
        }

    def recommend_career(self, education_level, years_experience, work_style, interests, skills):
        if self.career_vectorizer is None or self.career_matrix is None or self.career_df is None:
            return {"error": "Career engine not initialized"}

        user_text = f"{interests} {skills} {work_style} {education_level}"
        user_vec = self.career_vectorizer.transform([user_text])

        sim_scores = cosine_similarity(user_vec, self.career_matrix).flatten()
        top_indices = sim_scores.argsort()[::-1][:5]

        recommendations = []
        for idx in top_indices:
            row = self.career_df.iloc[idx]
            match_pct = round(float(sim_scores[idx]) * 100, 1)
            # Boost score based on dataset match score if available
            base_score = float(row.get('match_score', 80))
            final_score = min(98.5, round((match_pct * 0.6 + base_score * 0.4), 1))
            
            recommendations.append({
                "career_title": str(row.get('recommended_career', 'Data Specialist')),
                "industry": str(row.get('recommended_industry', 'Information Technology')),
                "match_score": final_score,
                "reasoning": str(row.get('reasoning', f"High compatibility based on your interests in {interests} and skills in {skills}.")),
                "alternative_recommendation": str(row.get('alternative_recommendation', 'Software Engineer'))
            })

        return {
            "top_recommendation": recommendations[0] if recommendations else None,
            "all_matches": recommendations
        }

ml_engine = MLEngine()
