import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from biblioteca_api.app import app
from biblioteca_api.app.models import Base
from biblioteca_api.app.main import app as fastapi_app
from app.main import app

# Configuración de base de datos para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Base de datos en memoria o en disco
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear las tablas para las pruebas
Base.metadata.create_all(bind=engine)

# Crear una instancia del cliente de prueba
@pytest.fixture(scope="module")
def client():
    # Configurar una sesión de base de datos para pruebas
    db = TestingSessionLocal()
    
    # Crear un cliente para realizar las solicitudes
    with TestClient(fastapi_app) as client:
        yield client
    db.close()

# Prueba de creación de un libro
def test_create_book(client):
    response = client.post(
        "/create/books/",
        json={
            "title": "Libro de prueba",
            "author": "Autor de prueba",
            "year": 2024,
            "editorial": "Editorial de prueba",
            "pages": 100
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "Book created successfully"
    assert "id" in data["data"]  

# Prueba para obtener todos los libros
def test_list_books(client):
    response = client.get("/get/books/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data  
    assert isinstance(data["data"], list)  

# Prueba para obtener un libro por ID
def test_get_book_by_id(client):
    # Primero crea un libro para probar la búsqueda
    create_response = client.post(
        "/create/books/",
        json={
            "title": "Libro de prueba",
            "author": "Autor de prueba",
            "year": 2024,
            "editorial": "Editorial de prueba",
            "pages": 100
        }
    )
    book_id = create_response.json()["data"]["id"] 

    # Obtener el libro por su ID
    response = client.get(f"/get/book/{book_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"][0]["id"] == book_id  
    assert data["data"][0]["title"] == "Libro de prueba"  # Verifica el título del libro

# Prueba para actualizar un libro
def test_update_book(client):
    # Crear un libro para actualizar
    create_response = client.post(
        "/create/books/",
        json={
            "title": "Libro viejo",
            "author": "Autor viejo",
            "year": 2022,
            "editorial": "Editorial vieja",
            "pages": 100
        }
    )
    book_id = create_response.json()["data"]["id"]

    # Actualizar el libro
    response = client.put(
        f"/put/books/{book_id}/",
        json={
            "title": "Libro actualizado",
            "author": "Autor actualizado",
            "year": 2023,
            "editorial": "Editorial nueva",
            "pages": 150
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "Book updated successfully"
    assert data["data"]["id"] == book_id  
    assert data["data"]["title"] == "Libro actualizado" 

# Prueba para eliminar un libro
def test_delete_book(client):
    # Crear un libro para eliminar
    create_response = client.post(
        "/create/books/",
        json={
            "title": "Libro a eliminar",
            "author": "Autor eliminar",
            "year": 2023,
            "editorial": "Editorial eliminar",
            "pages": 100
        }
    )
    book_id = create_response.json()["data"]["id"]

    # Eliminar el libro
    response = client.delete(f"/delete/book/{book_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "Book with id" in data["message"] 
