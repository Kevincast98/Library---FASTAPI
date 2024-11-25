from fastapi import FastAPI, HTTPException, Depends,status
from sqlalchemy.orm import Session
from app.models import Base, engine, Book, SessionLocal
from app.schemas import BookCreate, BookUpdate, BookResponse
from typing import List
from app.schemas import BookResponse
from typing import List
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.models import User, Book
from app.auth import get_password_hash, decode_token, OAuth2PasswordBearer
from app.schemas import UserCreate, UserResponse , UserLogin  
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth import verify_password, create_access_token  
import bcrypt
from fastapi import Query


Base.metadata.create_all(bind=engine)

app = FastAPI()


class BooksResponse(BaseModel):
    success: bool
    message: str
    data: List[BookResponse]

# Dependency para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



#//////////////////////////////// SERVICES  //////////////////////////////////



# ---------- REGISTER ----------



@app.post("/register/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hashear la contraseña del usuario
    hashed_password = get_password_hash(user.password)

    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ---------- TOKEN & LOGIN  ----------

# Esquema OAuth2 para leer el token de las solicitudes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependencia para obtener el usuario del token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        username = decode_token(token)  
        return username  
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or expired token")


@app.post("/token")
def login_for_access_token(form_data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == form_data.username).first()
    
   
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    
    access_token = create_access_token(data={"sub": user.username})
    
   
    return {"access_token": access_token, "token_type": "bearer"}


# ---------- BOOKS CRUD ----------


#CREATE_BOOK
# CREATE_BOOK
@app.post("/create/books/", status_code=201, summary="Create a Book", description="Crea un libro en la base de datos. Verifica si ya existe un libro con el mismo título y autor antes de proceder con la creación.")
def create_book(
    book: BookCreate, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user) 
):
    # Validar si ya existe un libro con el mismo título y autor
    existing_book = db.query(Book).filter(Book.title == book.title, Book.author == book.author).first()
    if existing_book:
        return {
            "success": False,
            "message": "Validation error",
            "detail": "A book with the same title and author already exists"
        }
    try:
        # Crear el libro
        db_book = Book(**book.dict())
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return {
            "success": True,
            "message": "Book created successfully",
            "data": db_book
        }
    except Exception as e:
        db.rollback()  
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the book: {str(e)}"
        )




# GET_ALLS_BOOKS
@app.get("/get/books/", response_model=BooksResponse, 
         summary="List all books", 
         description="Obtiene una lista de libros filtrados por autor, año, editorial o título. Se pueden usar parámetros opcionales para refinar la búsqueda.")
def list_books(
    author: Optional[str] = Query(None, description="Filtra los libros por autor. El valor puede ser una cadena parcial para una búsqueda de tipo 'LIKE'."),
    year: Optional[str] = Query(None, description="Filtra los libros por año de publicación. El valor debe ser un número entero."),
    editorial: Optional[str] = Query(None, description="Filtra los libros por editorial. El valor puede ser una cadena parcial para una búsqueda de tipo 'LIKE'."),
    title: Optional[str] = Query(None, description="Filtra los libros por título. El valor puede ser una cadena parcial para una búsqueda de tipo 'LIKE'."),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user) 
):
    """
    Obtiene una lista de libros, con filtros opcionales:
    - **author**: Autor del libro.
    - **year**: Año de publicación del libro.
    - **editorial**: Editorial del libro.
    - **title**: Título del libro.

    Si se proporcionan parámetros de búsqueda, se filtran los libros en base a esos parámetros.
    Si no se proporcionan filtros, devuelve todos los libros disponibles.
    """
    query = db.query(Book)

    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))

    if year:
        try:
            year = int(year)  # Convertir el valor de año a entero
            query = query.filter(Book.year == year)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid value for year. It must be a valid integer.")

    if editorial:
        query = query.filter(Book.editorial.ilike(f"%{editorial}%"))

    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))

    books = query.all()

    return {
        "success": True,
        "message": "Books retrieved successfully",
        "data": books
    }

#GET_BOOK_BY_ID
@app.get("/get/book/{book_id}/", response_model=BooksResponse,
         summary="Get book by ID",
         description="Obtiene un libro específico de la base de datos basado en el ID proporcionado. Si el libro no existe, devuelve un error 404.")
def get_book_by_id(
    book_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  
):
    """
    Obtiene un libro por su ID.
    
    - **book_id**: El ID único del libro en la base de datos.
    
    Si el libro no se encuentra, se devuelve un error 404.
    """
    # Obtener el libro de la base de datos
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    
    response_data = BooksResponse(
        success=True,
        message="Book retrieved successfully",
        data=[BookResponse(  
            title=book.title,
            author=book.author,
            year=book.year,
            editorial=book.editorial,
            pages=book.pages,
            id=book.id
        )]
    )
    
    return response_data

    
#EDIT_BOOK   
@app.put("/put/books/{book_id}/", response_model=BooksResponse,
         summary="Update book by ID",
         description="Actualiza los detalles de un libro específico en la base de datos utilizando el ID proporcionado. Si el libro no existe, devuelve un error 404. Si hay un problema de integridad en los datos, se devolverá un error 400.")
def update_book(
    book_id: int, 
    book: BookUpdate,  
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)  
):
    """
    Actualiza un libro por su ID.
    
    - **book_id**: El ID único del libro a actualizar.
    - **book**: Un objeto con los campos a actualizar, sólo los campos proporcionados serán modificados.
    
    Si el libro no se encuentra, se devuelve un error 404. Si los datos violan restricciones de integridad, se devuelve un error 400.
    """
    # Buscar el libro en la base de datos
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Actualizar los campos del libro
    for key, value in book.dict(exclude_unset=True).items():
        setattr(db_book, key, value)

    # Guardar cambios en la base de datos
    try:
        db.commit()
        db.refresh(db_book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error: a unique constraint was violated")

    # Respuesta de éxito
    return BooksResponse(
        success=True,
        message="Book updated successfully",
        data=[BookResponse(
            title=db_book.title,
            author=db_book.author,
            year=db_book.year,
            editorial=db_book.editorial,
            pages=db_book.pages,
            id=db_book.id
        )]
    )


# DELETE_BOOK
@app.delete("/delete/book/{book_id}/", response_model=BooksResponse,
            summary="Delete book by ID",
            description="Elimina un libro específico de la base de datos utilizando el ID proporcionado. Si el libro no existe, se devuelve un error 404. En caso de éxito, se devuelve un mensaje confirmando la eliminación.")
def delete_book(
    book_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)  # Validación del token
):
    """
    Elimina un libro por su ID.
    
    - **book_id**: El ID único del libro que se desea eliminar.
    
    Si el libro no se encuentra, se devuelve un error 404. Si la eliminación es exitosa, se devuelve el detalle del libro eliminado.
    """
    
    db_book = db.query(Book).filter(Book.id == book_id).first()
    
    if not db_book:
        return BooksResponse(
            success=False,
            message="Book not found",
            data=[]
        )
    
    
    deleted_book_data = BookResponse(
        title=db_book.title,
        author=db_book.author,
        year=db_book.year,
        editorial=db_book.editorial,
        pages=db_book.pages,
        id=db_book.id
    )
    
    # Eliminar el libro
    db.delete(db_book)
    db.commit()
    
    # Respuesta de éxito
    return BooksResponse(
        success=True,
        message=f"Book with id {book_id} has been deleted successfully",
        data=[deleted_book_data] 
    )