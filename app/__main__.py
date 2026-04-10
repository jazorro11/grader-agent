"""Run the demo server: ``python -m app``."""

from __future__ import annotations

import os

from app import create_app

if __name__ == "__main__":
    flask_app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    flask_app.run(debug=debug)
