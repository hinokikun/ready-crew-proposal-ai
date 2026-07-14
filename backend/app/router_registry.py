from fastapi import FastAPI

from app.routers import analytics as analytics_router
from app.routers import auth as auth_router
from app.routers import beautiful_ai as beautiful_ai_router
from app.routers import briefing as briefing_router
from app.routers import feedback as feedback_router
from app.routers import integrations as integrations_router
from app.routers import knowledge as knowledge_router
from app.routers import learning as learning_router
from app.routers import logs as logs_router
from app.routers import notifications as notifications_router
from app.routers import orchestrator as orchestrator_router
from app.routers import organizations as organizations_router
from app.routers import pilot as pilot_router
from app.routers import presentation_review as presentation_review_router
from app.routers import projects as projects_router
from app.routers import prompts as prompts_router
from app.routers import proposal_optimization as proposal_optimization_router
from app.routers import quality_gates as quality_gates_router
from app.routers import releases as releases_router
from app.routers import reviews as reviews_router
from app.routers import users as users_router
from app.routers import workspace as workspace_router


def include_application_routers(app: FastAPI) -> None:
    app.include_router(auth_router.router)
    app.include_router(users_router.router)
    app.include_router(briefing_router.router)
    app.include_router(notifications_router.router)
    app.include_router(orchestrator_router.router)
    app.include_router(organizations_router.router)
    app.include_router(pilot_router.router)
    app.include_router(projects_router.router)
    app.include_router(logs_router.router)
    app.include_router(feedback_router.router)
    app.include_router(integrations_router.router)
    app.include_router(analytics_router.router)
    app.include_router(knowledge_router.router)
    app.include_router(learning_router.router)
    app.include_router(prompts_router.router)
    app.include_router(proposal_optimization_router.router)
    app.include_router(presentation_review_router.router)
    app.include_router(workspace_router.router)
    app.include_router(reviews_router.router)
    app.include_router(quality_gates_router.router)
    app.include_router(releases_router.router)
    app.include_router(beautiful_ai_router.router)
