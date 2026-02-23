from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field
app=FastAPI()



#############################################################################
#Tworzymy klasę książki - żeby móc dodawać nową, przez inicjalizację obiektu
#############################################################################


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int

    def __init__(self, id, title, author, description, rating):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating


BOOKS = [
    Book(1, 'Computer Science Pro', 'codingwithroby', 'A very nice book!', 5),
    Book(2, 'Be Fast with FastAPI', 'codingwithroby', 'A great book!', 5),
    Book(3, 'Master Endpoints', 'codingwithroby', 'A awesome book!', 5),
    Book(4, 'HP1', 'Author 1', 'Book Description', 2),
    Book(5, 'HP2', 'Author 2', 'Book Description', 3),
    Book(6, 'HP3', 'Author 3', 'Book Description', 1)
]



class BookRequest(BaseModel):
    id: Optional[int] = Field(description='ID is not needed on create', default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)
    published_date: int = Field(gt=1999, lt=2031)

   








@app.get("/books")
async def read_all_books():
    return BOOKS

# Body() nie dodaje żadnej walidacji na wejściu, trzeba to robić osobno - pydantics (modelowanie i parsowanie danych wejściowych - ma dobry error handling)
# Walidacja przez pydantic a później przejście z klasy BookRequest na Book
# Walidację można robić przez kwargs (**) tylko konstruktory klas muszą być takie same 


@app.post("/create_book")
# W celu walidacji zmieniamy Body (bo nie idzie prosto do BOOKS) na BookRequest
#async def create_book(book_request= Body()):
async def create_book(book_request: BookRequest):
    new_book=Book(**book_request.model_dump())
    BOOKS.append(new_book)
