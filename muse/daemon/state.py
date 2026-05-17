import json
from loguru import logger
from muse.utils.paths import get_state_file

class StateManager:
    @staticmethod
    def save(queue_manager, controller):
        state_file = get_state_file()
        try:
            # We use properties from mpv controller if available
            volume = 100
            position = 0
            if controller.mpv:
                try:
                    volume = controller.mpv.volume
                    position = controller.mpv.time_pos
                except:
                    pass

            state = {
                "queue": queue_manager.to_dict(),
                "volume": volume,
                "position": position
            }
            with open(state_file, "w") as f:
                json.dump(state, f)
            logger.debug(f"Saved state to {state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    @staticmethod
    def load():
        state_file = get_state_file()
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
            return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
