
import app.session
import uvicorn

def run():
    uvicorn.run(
        "app:api",
        host=app.session.config.API_HOST,
        port=app.session.config.API_PORT,
        reload=app.session.config.RELOAD,
        server_header=False,
        log_config=None,
    )

if __name__ == "__main__":
    run()
