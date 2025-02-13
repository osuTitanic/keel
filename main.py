
import uvicorn
import config

def run():
    uvicorn.run(
        "app:api",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.RELOAD,
        server_header=False,
        log_config=None,
    )

if __name__ == "__main__":
    run()
