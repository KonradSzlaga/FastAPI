
from fastapi import FastAPI
import models 
from database import engine
from routers import auth, todos, admin, users


app = FastAPI()

# poniższe mówi: utwórz wszystkie tabele w bazie danych, jeśli jeszcze nie istnieją
"""
Weź wszystkie modele SQLAlchemy dziedziczące po Base 
i utwórz odpowiadające im tabele w bazie danych przy użyciu połączenia engine.

SQLAlchemy:
    patrzy na Base.metadata
    sprawdza jakie są modele
    generuje SQL
    wykonuje go na bazie przez engine

    
W tym przypadku uruchamiamy to przez:
uvicorn main:app --reload 

"""
models.Base.metadata.create_all(bind=engine)

# dołączamy router
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(users.router)

