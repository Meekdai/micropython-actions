include("$(MPY_DIR)/extmod/uasyncio/manifest.py")
freeze("$(BOARD_DIR)/modules", ("htmlserver.py", "logging.py", "tmc5130.py", "ws.py"))
