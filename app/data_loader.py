import os
import pandas as pd
import numpy as np

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Dataset')

class DataLoader:
    def __init__(self):
        self.datasets = {}
        self.load_all()

    def load_all(self):
        files = {
            'resume': '01_resume_analysis_dataset.csv',
            'skill_gap': '02_skill_gap_analysis_dataset.csv',
            'roadmap': '03_roadmap_generator_dataset.csv',
            'interview': '04_interview_questions_dataset.csv',
            'linkedin': '05_linkedin_review_dataset.csv',
            'github': '06_github_review_dataset.csv',
            'salary': '07_salary_prediction_dataset.csv',
            'career': '08_career_recommendation_dataset.csv'
        }
        for key, filename in files.items():
            path = os.path.join(DATASET_DIR, filename)
            if os.path.exists(path):
                # Sample up to 10,000 rows per dataset for Render 512MB RAM cloud compatibility
                df = pd.read_csv(path, nrows=10000, low_memory=False)
                self.datasets[key] = df
                print(f"Loaded {key}: {len(df)} rows.")

    def get_unique_options(self):
        options = {
            'industries': [],
            'job_titles': [],
            'target_roles': [],
            'education_levels': [],
            'skills': [],
            'countries': []
        }
        
        if 'salary' in self.datasets:
            df = self.datasets['salary']
            options['industries'] = sorted(df['industry'].dropna().unique().tolist())
            options['job_titles'] = sorted(df['job_title'].dropna().unique().tolist())
            options['education_levels'] = sorted(df['education_level'].dropna().unique().tolist())
            options['countries'] = sorted(df['country'].dropna().unique().tolist()[:50])

        if 'skill_gap' in self.datasets:
            df = self.datasets['skill_gap']
            targets = df['target_role'].dropna().unique().tolist()
            options['target_roles'] = sorted(list(set(options['job_titles'] + targets)))
            
        if 'career' in self.datasets:
            df = self.datasets['career']
            # extract unique skills
            all_skills = set()
            for skill_str in df['current_skills'].dropna():
                skills = [s.strip() for s in str(skill_str).split(',')]
                all_skills.update(skills)
            options['skills'] = sorted(list(all_skills))[:100]

        return options

data_loader = DataLoader()
