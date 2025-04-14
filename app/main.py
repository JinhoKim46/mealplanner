from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI + Docker 환경 정상 작동 중!"}
