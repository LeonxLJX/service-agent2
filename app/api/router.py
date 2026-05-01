from fastapi import APIRouter
from app.api.endpoints import mimo, intent, knowledge, order

api_router = APIRouter()

api_router.include_router(mimo.router)
api_router.include_router(intent.router)
api_router.include_router(knowledge.router)
api_router.include_router(order.router)
