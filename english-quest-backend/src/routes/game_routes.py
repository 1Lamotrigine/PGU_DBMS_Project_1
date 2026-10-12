from fastapi import APIRouter

from src.controllers import game_controller

router = APIRouter(tags=["Game"])

router.add_api_route("/missions/{mission_id}/start", game_controller.start_mission_attempt, methods=["POST"])
router.add_api_route("/missions/{mission_id}/submit-tests", game_controller.submit_mission_tests, methods=["POST"])
router.add_api_route(
    "/missions/{mission_id}/submit-pronunciation",
    game_controller.submit_mission_pronunciation,
    methods=["POST"],
)
router.add_api_route("/missions/{mission_id}/submit-game", game_controller.submit_mission_game, methods=["POST"])
