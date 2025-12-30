import os

import uvicorn

from webapp.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("BACKEND_PORT") or os.environ.get("PORT") or 8000)
    uvicorn.run("webapp.main:app", host="127.0.0.1", port=port, reload=True)
