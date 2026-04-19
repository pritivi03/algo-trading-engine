import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from apps.api.routes import account, runs, strategies

load_dotenv()

app = FastAPI(title="Algo Trading Engine")
app.include_router(strategies.router)
app.include_router(runs.router)
app.include_router(account.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8080, reload=True)