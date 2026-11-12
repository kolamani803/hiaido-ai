from alembic import context
from sqlalchemy import engine_from_config, pool
import os

config = context.config
url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
# Match the runtime SQLAlchemy driver installed in the backend image.
if url.startswith("postgres://"):
    url = "postgresql+psycopg://" + url[len("postgres://"):]
elif url.startswith("postgresql://"):
    url = "postgresql+psycopg://" + url[len("postgresql://"):]
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))

def run_migrations_offline():
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config({"sqlalchemy.url": url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
