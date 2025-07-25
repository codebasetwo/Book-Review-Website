from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db.main import init_db
from src.auth.routers import auth_router
from src.books.routers import book_router
from src.reviews.routers import review_router
from src.tags.routers import tags_router
from .errors import register_all_errors
from .middleware import register_middleware


@asynccontextmanager
async def life_span(app: FastAPI):
    print("server is starting..")
    await init_db()
    yield
    print("Server stopped!")


description = """
A REST API for a book review web service.

This REST API is able to;
- Create Read Update And delete books
- Add reviews to books
- Add tags to Books e.t.c.
    """

version = "v1"
app = FastAPI(
    title="Book-worm",
    version=version,
    description=description,
    license_info={"name": "MIT License",
                   "url": "https://opensource.org/license/mit"
                   },
    #lifespan=life_span
    contact= {
        "email": "nuaemeka@gmail.com",
        "name": "Nnaemeka Nwankwo",
        }
)

register_all_errors(app)
register_middleware(app)

app.include_router(book_router, prefix=f"/api/{version}/books", tags=["books"])
app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=["auth"])
app.include_router(review_router, prefix=f"/api/{version}/reviews", tags=["reviews"])
app.include_router(tags_router, prefix=f"/api/{version}/tags", tags=["tags"])