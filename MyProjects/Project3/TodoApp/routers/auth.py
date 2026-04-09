# Importy związane z datą i czasem.
# Są potrzebne do ustawiania ważności tokenu JWT.
from datetime import datetime, timedelta, timezone

# Annotated pozwala ładnie opisać zależności w FastAPI.
from typing import Annotated

# Session to sesja połączenia z bazą danych SQLAlchemy.
from sqlalchemy.orm import Session

# APIRouter służy do grupowania endpointów,
# Depends do wstrzykiwania zależności,
# HTTPException do zwracania kontrolowanych błędów HTTP.
from fastapi import APIRouter, Depends, HTTPException

# BaseModel służy do definiowania schematów danych wejściowych i wyjściowych.
# Field tutaj akurat nie jest używany.
from pydantic import BaseModel, Field

# Model tabeli users z pliku models.py
from models import Users

# CryptContext z passlib służy do bezpiecznego haszowania i weryfikacji haseł.
from passlib.context import CryptContext

# SessionLocal to fabryka sesji bazy danych.
from database import SessionLocal

# Gotowe kody statusów HTTP, np. 401, 201 itd.
from starlette import status

# OAuth2PasswordRequestForm pozwala odebrać login i hasło w standardzie OAuth2.
# OAuth2PasswordBearer pobiera token z nagłówka Authorization: Bearer ...
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

# jose.jwt służy do tworzenia i dekodowania tokenów JWT.
# JWTError łapie błędy związane z nieprawidłowym tokenem.
from jose import jwt, JWTError


# Tworzymy router dla endpointów związanych z autoryzacją.
# prefix='/auth' oznacza, że wszystkie ścieżki tutaj zaczną się od /auth
# tags=['auth'] grupuje je w dokumentacji Swaggera.
router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


# SECRET_KEY to tajny klucz używany do podpisywania tokenów JWT.
# Dzięki temu serwer może sprawdzić, czy token został wystawiony przez niego
# i czy nie został podmieniony.
SECRET_KEY = '8f3c7d2a9b1e4f6c0d5a8e2b7c1f9a3d6e4b2c7a9d0f1e6b3c8a5d2f7e1b9c4'

# ALGORITHM określa algorytm podpisywania tokenu.
# HS256 jest popularny i prosty do użycia przy projektach backendowych.
ALGORITHM = 'HS256'


# Konfiguracja haszowania haseł.
# Zamiast przechowywać hasło w bazie w czystej postaci,
# zapisujemy jego hash.
# To zwiększa bezpieczeństwo — nawet jeśli ktoś wykradnie bazę,
# nie zobaczy od razu prawdziwych haseł.
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


# OAuth2PasswordBearer mówi FastAPI:
# "token autoryzacyjny będzie przekazywany przez klienta jako Bearer token".
#
# tokenUrl='auth/token' oznacza, że endpoint do logowania/tokenu
# znajduje się pod adresem /auth/token.
#
# To jest ważne głównie dla Swagger UI i mechanizmu autoryzacji w FastAPI.
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


# Schemat danych wejściowych do tworzenia użytkownika.
# FastAPI automatycznie sprawdzi, czy klient wysłał poprawne pola.
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str


# Schemat odpowiedzi dla endpointu logowania.
# Dzięki response_model=Token dokumentacja wie,
# jaki format danych zostanie zwrócony.
class Token(BaseModel):
    access_token: str
    token_type: str


# Funkcja tworząca sesję do bazy danych.
# Używamy yield, bo FastAPI traktuje to jako zależność "otwórz -> użyj -> zamknij".
#
# Dlaczego tak?
# Bo każda prośba HTTP powinna dostać własną sesję bazy,
# a po zakończeniu obsługi trzeba ją zamknąć, żeby nie było wycieków połączeń.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Tu tworzymy skrót typu zależności.
# Zamiast za każdym razem pisać:
# db: Session = Depends(get_db)
# można używać db: db_dependency
db_dependency = Annotated[Session, Depends(get_db)]


# Funkcja sprawdzająca, czy użytkownik istnieje
# i czy podane hasło zgadza się z hashem w bazie.
def authenticate_user(username: str, password: str, db):
    # Szukamy użytkownika po username.
    user = db.query(Users).filter(Users.username == username).first()

    # Jeśli nie ma takiego użytkownika -> zwracamy False.
    if not user:
        return False

    # verify porównuje zwykłe hasło z hashem z bazy.
    # Nie porównujemy tekstów 1:1, bo hasło w bazie jest zahashowane.
    if not bcrypt_context.verify(password, user.hashed_password):
        return False

    # Jeśli wszystko się zgadza, zwracamy obiekt użytkownika.
    return user


# Funkcja tworząca token JWT.
def create_access_token(username: str, user_id: int, role:str, expires_delta: timedelta):
    # Dane, które zapisujemy w tokenie.
    # 'sub' (subject) zwyczajowo oznacza główny identyfikator użytkownika.
    # 'id' to nasze dodatkowe pole.
    encode = {'sub': username, 'id': user_id, 'role':role}

    # Ustawiamy datę wygaśnięcia tokenu.
    # Użycie timezone.utc jest dobrą praktyką,
    # bo eliminuje problemy ze strefami czasowymi.
    expires = datetime.now(timezone.utc) + expires_delta

    # Dodajemy do payloadu pole 'exp', które JWT rozumie jako czas ważności.
    encode.update({'exp': expires})

    # Zwracamy podpisany token jako string.
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# Funkcja pobierająca aktualnego użytkownika na podstawie tokenu.
# FastAPI automatycznie wyciąga token z nagłówka Authorization.
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):

    try:
        # Dekodujemy token.
        # Jeśli token jest nieprawidłowy, zmieniony albo wygasł,
        # jwt.decode rzuci wyjątek.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Odczytujemy dane zapisane wcześniej w tokenie.
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role:str = payload.get('role')

        # Jeśli brakuje wymaganych danych, uznajemy token za nieważny.
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials'
            )

        # Zwracamy dane użytkownika wyciągnięte z tokenu.
        # Często potem używa się tego w chronionych endpointach.
        return {
            "username": username,
            "id": user_id,
            "user_role":user_role
        }

    # Jeśli dekodowanie tokenu się nie powiedzie,
    # zwracamy 401 Unauthorized.
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials'
        )


# Endpoint do tworzenia użytkownika.
# POST /auth/
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    db: db_dependency,
    create_user_request: CreateUserRequest
):
    try:
        # Tworzymy obiekt modelu Users na podstawie danych wejściowych.
        create_user_model = Users(
            email=create_user_request.email,
            username=create_user_request.username,
            first_name=create_user_request.first_name,
            last_name=create_user_request.last_name,

            # Hasło zapisujemy jako hash, nigdy jako czysty tekst.
            hashed_password=bcrypt_context.hash(create_user_request.password),

            role=create_user_request.role,
            is_active=True,
            phone_number=create_user_request.phone_number
        )

        # Dodajemy nowy rekord do sesji.
        db.add(create_user_model)

        # Zapisujemy zmiany do bazy.
        db.commit()

        # Odświeżamy obiekt z bazy, żeby np. pobrać wygenerowane id.
        db.refresh(create_user_model)

        # Zwracamy prostą odpowiedź.
        return {"message": "User created", "id": create_user_model.id}

    except Exception as e:
        # Jeśli coś pójdzie nie tak, cofamy transakcję,
        # żeby baza nie została w niepełnym stanie.
        db.rollback()

        # Wypisujemy błąd do konsoli.
        print("BŁĄD:", e)

        # Podnosimy wyjątek dalej.
        # W praktyce w produkcji lepiej zwrócić własny kontrolowany komunikat,
        # zamiast zostawiać surowy wyjątek.
        raise


# Endpoint logowania i generowania tokenu JWT.
# POST /auth/token
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    # Sprawdzamy, czy username i password są poprawne.
    user = authenticate_user(form_data.username, form_data.password, db)

    # Jeśli nie, zwracamy 401.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials'
        )

    # Jeśli dane są poprawne, tworzymy token ważny 20 minut.
    token = create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=20)
    )

    # Zwracamy token w standardowym formacie OAuth2.
    return {
        "access_token": token,
        "token_type": "bearer"
    }



"""

CryptContext — haszowanie i sprawdzanie haseł
OAuth2PasswordBearer — pobieranie tokenu z nagłówka
OAuth2PasswordRequestForm — odbieranie loginu i hasła w standardzie OAuth2
create_access_token() — tworzenie JWT
get_current_user() — odczyt użytkownika z tokenu
get_db() — otwieranie i zamykanie sesji bazy danych
response_model=Token — określenie formatu odpowiedzi


"""