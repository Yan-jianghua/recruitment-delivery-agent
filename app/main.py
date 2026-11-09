from fastapi import FastAPI

app = FastAPI(title="recruitment Delivery Agent")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}