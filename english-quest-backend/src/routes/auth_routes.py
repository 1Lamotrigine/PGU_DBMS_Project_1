from fastapi import APIRouter, Depends, status

from src.controllers import auth_controller
from src.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

router.add_api_route("/register", auth_controller.register, methods=["POST"], status_code=status.HTTP_201_CREATED)
router.add_api_route("/login", auth_controller.login, methods=["POST"])
router.add_api_route("/google", auth_controller.google_login, methods=["POST"])
router.add_api_route("/me", auth_controller.me, methods=["GET"])


calibration_router = APIRouter(prefix="/calibration", tags=["Calibration"])
calibration_router.add_api_route("/questions", auth_controller.calibration_questions, methods=["GET"])
calibration_router.add_api_route("/submit", auth_controller.calibration_submit, methods=["POST"])
