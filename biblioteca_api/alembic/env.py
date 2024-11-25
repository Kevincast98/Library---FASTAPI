from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from app.models import Base, DATABASE_URL  # Importa tu modelo y la URL de conexión

# Configuración de logs
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asigna la metadata de los modelos
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Ejecuta migraciones en modo 'offline'.
    Configura el contexto con solo una URL.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Ejecuta migraciones en modo 'online'.
    Crea un Engine y asocia la conexión al contexto.
    """
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
