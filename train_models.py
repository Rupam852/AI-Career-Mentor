import sys
from app.ml_engine import ml_engine

def main():
    print("=== Initializing AI Career Mentor Datasets & ML Models ===")
    ml_engine.train_or_load_models()
    print("=== Training Complete & Models Ready ===")

if __name__ == "__main__":
    main()
