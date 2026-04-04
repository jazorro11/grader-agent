# Punto de entrada: `python app.py`. Los tests importan `grader_agent.web.app`.

import os

from grader_agent.web.app import app

if __name__ == "__main__":
    _debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=_debug)
