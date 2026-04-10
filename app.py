"""Legacy entrypoint; prefer ``python -m app`` or ``flask --app app:create_app run``."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    import os

    _debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=_debug)
