from fastapi import FastAPI

from backend.routes.translate import router as translate_router

app = FastAPI(
    title="Medical Translation API"
)

app.include_router(translate_router)