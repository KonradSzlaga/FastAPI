# FastAPI
# Główna klasa frameworka.
# Tworzy Twoją aplikację webową (API).
from fastapi import Body, FastAPI

# Tworzę instancję aplikacji
app = FastAPI()

from jsons import BOOKS

# zwraca cokolwiek
@app.get("/api-endpoint")
async def first_api():
    return{"message":"Watashiwa Wasabi-san"}

#Zwraca liste wszystkich książek jakie mamy
@app.get("/books")
async def get_books():
    return BOOKS

########################################################################################################################

# Path parameters
#   - dołaczane do URL
#   - służą do lokalizacji zasobu

@app.get("/books/{book_title}")
async def get_books(book_title: str):
    for book in BOOKS:
        if book.get('title').casefold() == book_title.casefold():
            return book



########################################################################################################################

# Query parameters
#   - dołaczane do URL
#   - służą do lokalizacji zasobu

#   /books/?category=science

@app.get("/books/")
async def read_category_by_query(category: str):
    books_to_return = []
    for book in BOOKS:
        if book.get('category').casefold() == category.casefold():
            books_to_return.append(book)
    return books_to_return


########################################################################################################################

# Path query parameters together 
#   - dołaczane do URL
#   - służą do lokalizacji zasobu

@app.get("/books/{book_title}/")
async def get_book_path_and_query(book_title: str,category: str):
    books_to_return = []
    for book in BOOKS:
        if book.get('category').casefold() == category.casefold() and \
            book.get('title').casefold() == book_title.casefold():
            books_to_return.append(book)
    return books_to_return





################################################        POST        ################################################

# Has body in request
#


@app.post("/books/create_book")
async def create_book(new_book=Body()):
    BOOKS.append(new_book)
    

################################################        PUT        ################################################

# Can have body in request
# Used to update records


@app.put("/books/update_book")
async def update_book(updated_book=Body()):
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold()==updated_book.get("title").casefold():
            BOOKS[i] = updated_book


################################################        DELETE        ################################################

# Used to delete records


@app.delete("/books/delete_book/{book_title}")
async def delete_book(book_title:str):
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold()==book_title.casefold():
            BOOKS.pop(i)
            break




