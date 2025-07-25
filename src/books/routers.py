from fastapi import APIRouter, Depends, status
from typing import List
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession 


from .schemas import BookUpdateModel, Books, BookCreateModel, BookDetailModel
from src.db.main import get_session
from src.books.service import BookService
from src.auth.dependencies import RoleChecker
from src.auth.dependencies import AccessTokenBearer
from src.errors import BookNotFound

book_service = BookService()
book_router = APIRouter()
access_token_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(["admin", "user"]))

@book_router.get("/", response_model=List[Books], dependencies=[role_checker] )
async def get_all_books(session: AsyncSession= Depends(get_session),
                        token_details: dict =Depends(access_token_bearer)
                        ):
    return await book_service.get_all_books(session)

@book_router.get(
    "/user/{user_uid}", response_model=List[Books], dependencies=[role_checker]
)
async def get_user_book_submissions(
    user_uid: str,
    session: AsyncSession = Depends(get_session),
    _: dict = Depends(access_token_bearer),
):
    books = await book_service.get_user_books(user_uid, session)
    return books



@book_router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[role_checker])
async def create_a_book(book: BookCreateModel,
                        session: AsyncSession=Depends(get_session),
                        token_details: dict =Depends(access_token_bearer)):
    user_uid = token_details.get("user")["user_uid"]
    new_book = await book_service.create_book(book, user_uid, session)
    return new_book

    # data = book.model_dump()
    # in_mem_book_db.append(data)
    # return data


@book_router.get("/{book_uid}", response_model= BookDetailModel,dependencies=[role_checker])
async def get_a_book(book_uid: str,
                     session: AsyncSession= Depends(get_session),
                     token_details: dict =Depends(access_token_bearer)):
    
    book = await book_service.get_book(book_uid, session)
    if book:
        return book
    else: 
        raise BookNotFound()
    #raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

@book_router.patch("/{book_uid}", dependencies=[role_checker])
async def update_book(book_uid: str, update_book: BookUpdateModel, 
                      session: AsyncSession= Depends(get_session),
                      token_details: dict =Depends(access_token_bearer)):
    update_book = await book_service.update_book(book_uid, update_book, session)
    if update_book:
        return update_book

    raise BookNotFound()

@book_router.delete("/{book_uid}", 
                    status_code=status.HTTP_204_NO_CONTENT,
                    dependencies=[role_checker]
                    )
async def delete_book(book_uid: str, 
                      session: AsyncSession= Depends(get_session),
                      token_details: dict =Depends(access_token_bearer)):
    
    book = await book_service.delete_book(book_uid, session)
    if isinstance(book, dict):
        return
    else:
        raise BookNotFound()
    
    # for book in in_mem_book_db:
    #     if book["id"] == book_uid:
    #         in_mem_book_db.remove(book)