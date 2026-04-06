from __future__ import annotations

from support_ops_env.server.app import app


# Compatibility launcher for validators expecting server/app.py in repo root.
def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()
