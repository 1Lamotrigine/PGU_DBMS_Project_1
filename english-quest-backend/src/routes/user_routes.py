from fastapi import APIRouter

from src.controllers import user_controller

router = APIRouter(prefix="/users", tags=["Users"])

router.add_api_route("/me/progress", user_controller.my_progress, methods=["GET"])


students_router = APIRouter(prefix="/students", tags=["Students"])
students_router.add_api_route("/{student_id}/progress-preview", user_controller.student_progress_preview, methods=["GET"])
