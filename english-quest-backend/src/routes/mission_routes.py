from fastapi import APIRouter, Depends

from src.controllers import mission_controller
from src.middleware.role_middleware import require_roles

router = APIRouter(prefix="/missions", tags=["Missions"])

teacher_only = [Depends(require_roles("teacher"))]

# Read
router.add_api_route("/recommended", mission_controller.recommended_missions, methods=["GET"])
router.add_api_route("/{mission_id}/vocabulary", mission_controller.mission_vocabulary, methods=["GET"])
router.add_api_route("/{mission_id}", mission_controller.mission_detail, methods=["GET"])

# Mission CRUD (teacher)
router.add_api_route("", mission_controller.mission_create, methods=["POST"], dependencies=teacher_only)
router.add_api_route("/{mission_id}", mission_controller.mission_update, methods=["PUT"], dependencies=teacher_only)
router.add_api_route("/{mission_id}", mission_controller.mission_delete, methods=["DELETE"], dependencies=teacher_only)

# Task CRUD (teacher)
router.add_api_route(
    "/{mission_id}/tasks", mission_controller.task_create, methods=["POST"], dependencies=teacher_only
)

# Question / Option CRUD (teacher) — top-level resources
router.add_api_route("/tasks/{task_id}", mission_controller.task_update, methods=["PUT"], dependencies=teacher_only)
router.add_api_route("/tasks/{task_id}", mission_controller.task_delete, methods=["DELETE"], dependencies=teacher_only)
router.add_api_route(
    "/tasks/{task_id}/questions", mission_controller.question_create, methods=["POST"], dependencies=teacher_only
)
router.add_api_route(
    "/questions/{question_id}", mission_controller.question_update, methods=["PUT"], dependencies=teacher_only
)
router.add_api_route(
    "/questions/{question_id}", mission_controller.question_delete, methods=["DELETE"], dependencies=teacher_only
)
router.add_api_route(
    "/questions/{question_id}/options", mission_controller.option_create, methods=["POST"], dependencies=teacher_only
)
router.add_api_route(
    "/options/{option_id}", mission_controller.option_update, methods=["PUT"], dependencies=teacher_only
)
router.add_api_route(
    "/options/{option_id}", mission_controller.option_delete, methods=["DELETE"], dependencies=teacher_only
)


levels_router = APIRouter(prefix="/levels", tags=["Levels"])
levels_router.add_api_route("", mission_controller.levels, methods=["GET"])

# Level vocabulary (teacher-managed)
levels_router.add_api_route(
    "/{level_id}/vocabulary", mission_controller.level_vocabulary_list, methods=["GET"], dependencies=teacher_only
)
levels_router.add_api_route(
    "/{level_id}/vocabulary", mission_controller.vocabulary_create, methods=["POST"], dependencies=teacher_only
)

vocabulary_router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])
vocabulary_router.add_api_route(
    "/{vocab_id}", mission_controller.vocabulary_update, methods=["PUT"], dependencies=teacher_only
)
vocabulary_router.add_api_route(
    "/{vocab_id}", mission_controller.vocabulary_delete, methods=["DELETE"], dependencies=teacher_only
)
