from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import config
import models  # noqa: F401  (imported so Base knows about the tables)
from database import Base, engine
from routers.tests import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prep App")
app.include_router(router)

# Keep this last: a mount at "/" catches every path the routes above don't match.
app.mount(
    "/",
    StaticFiles(directory=config.BASE_DIR / "static", html=True),
    name="static",
)