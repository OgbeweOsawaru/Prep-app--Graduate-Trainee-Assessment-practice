from fastapi import FastAPI

from routers.tests import router

app = FastAPI(title="Prep App")
app.include_router(router)
