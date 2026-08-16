import sys
import uvicorn
from app.ml_engine import ml_engine

def main():
    print("==================================================")
    print("   AI CAREER MENTOR - ML & INTELLIGENCE PLATFORM  ")
    print("==================================================")
    print("Starting FastAPI Server at http://127.0.0.1:8000 ...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
