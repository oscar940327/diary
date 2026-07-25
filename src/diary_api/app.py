from typing import Literal, TypedDict

from fastapi import FastAPI


class HealthResponse(TypedDict):
    service: Literal["diary-api"]
    status: Literal["ready"]


app = FastAPI(title="Diary API")


@app.get("/health")
def health() -> HealthResponse:
    return {
        "service": "diary-api",
        "status": "ready",
    }
