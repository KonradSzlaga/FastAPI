from typing import Optional

# Path - do walidacji żeby walidować Path parameters
# Query - do walidacji żeby walidować Query parameters
# HTTPException - do zwracania odpowiedzniego statusu w zależności co się stało / nie stało

from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel, Field

# Zeby pokazywać status code jak jest OK
from starlette import status

app=FastAPI()


# ŹLE

# @app.get("/books/{book_id}")
# @app.get("/books/{book_rating}")
# FastAPI nie odróżni ich.

"""

Z zasady najpierw endpointy ze statyczną ścieżką a dopiero później z parametrami 

@app.get("/books/mybooks")
async def read_my_books():
    return BOOKS

@app.get("/books/{book_id}")
async def read_book(book_id: int):
    return book_id

1️⃣ /books
2️⃣ /books/something
3️⃣ /books/something/{param}
4️⃣ /books/{param}



"""

#############################################################################
# Tworzymy klasę książki - żeby móc dodawać nową, przez inicjalizację obiektu
#############################################################################


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id, title, author, description, rating, published_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


BOOKS = [
    Book(1, 'Computer Science Pro', 'codingwithroby', 'A very nice book!', 5, 2005),
    Book(2, 'Be Fast with FastAPI', 'codingwithroby', 'A great book!', 5, 2006),
    Book(3, 'Master Endpoints', 'codingwithroby', 'A awesome book!', 5, 2010),
    Book(4, 'HP1', 'Author 1', 'Book Description', 2, 2010),
    Book(5, 'HP2', 'Author 2', 'Book Description', 3, 2001),
    Book(6, 'HP3', 'Author 3', 'Book Description', 1, 2020)
]



class BookRequest(BaseModel):
    # Typujemy dane, a jak będą innego typu to dostaniemy error: 422 Unprocessable Entity
    # Możemy dodać wartości domyślne do pól - robimy to przez model_confg - bedzie to podane w 'Example Values' w swagger UI

    id: Optional[int] = Field(description='ID is not needed on create', default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)
    published_date: int = Field(gt=1999, lt=2031)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new book",
                "author": "codingwithroby",
                "description": "A new description of a book",
                "rating": 5,
                'published_date': 2029
            }
        }
    }
   

#############################################################################
# Funkcje
#############################################################################

def find_book_id(book:Book):
    
    #Krótki kod
    book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1 
    
    # długi kod
    # if len(BOOKS) > 0:
    #     book.id = BOOKS[-1].id + 1
    # else:
    #     book.id = 1

    return book














#############################################################################
# Endpointy
#############################################################################

@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_books():
    return BOOKS




@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
# Dostaemy się po book.id bo tablica BOOKS ma w sobie obiekty typu Book - dlatego po kropce
# dodajemy walidację na id żeby było > 0
async def read_book(book_id:int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
    
    raise HTTPException(status_code=404, detail='Item not found - there is not book with that id.')


@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)
    return books_to_return
    



# Body() nie dodaje żadnej walidacji na wejściu, trzeba to robić osobno - pydantics (modelowanie i parsowanie danych wejściowych - ma dobry error handling)
# Walidacja przez pydantic a później przejście z klasy BookRequest na Book
# Walidację można robić przez kwargs (**) tylko konstruktory klas muszą być takie same 


@app.post("/create_book", status_code=status.HTTP_201_CREATED)
# W celu walidacji zmieniamy Body (bo nie idzie prosto do BOOKS) na BookRequest
# async def create_book(book_request= Body()):
async def create_book(book_request: BookRequest):
    new_book=Book(**book_request.model_dump())
    #Podając funckję find_book_id tutaj nadpisujemy id dane przez użytkownika na właściwe
    BOOKS.append(find_book_id(new_book))


@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    #update robimy po book_id - ale z racji że pydantic w preview nie wyświetli id do wprowadzenia to musimy wziąć json z /books
    # flaga book changed - żeby w zależności odtego zwracac poprawny status
    
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:
            BOOKS[i] = book
            book_changed = True

    if not book_changed:
        raise HTTPException(status_code=404, detail='Item not found - there is not book with that id.')



@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id:int = Path(gt=0)):

    book_deleted = False
    for i in range(len(BOOKS)):
        #jeżeli id element 'i' w BOOKS
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_deleted = True
            break
    if not book_deleted:
        raise HTTPException(status_code=404, detail='Item not found - there is not book with that id.')


@app.get("/books/filter/", status_code=status.HTTP_200_OK)
async def read_book_by_publish_date(published_date: int = Query(gt=1999, lt=2031)):
    book_updated = False
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            books_to_return.append(book)
            book_updated = True
    if not book_updated:
            raise HTTPException(status_code=404, detail='Item not found - there are no books with that published date.')
    else:
        return books_to_return