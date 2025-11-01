from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Kuma Backend")

class Query(BaseModel):
    text: str

@app.post("/query")
def query(q: Query):
    text = q.text.strip()
    if not text:
        return {"reply": "I didn't catch that. Please say or type something."}
    return {"reply": f"Kuma says: You said '{text}'"}
