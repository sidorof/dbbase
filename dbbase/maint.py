# dbbase/maint.py
"""
This module implements maintenance tools for creating and deleting/dropping
databases.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from .utils import _is_sqlite


def create_database(config, dbname, superuser=None):
    """
    Creates a new database.

    Default:
        create_database(config, dbname)

    Note that if a superuser is included in the config, that user must have
    permissions to create a database.

    Args:
        config: (str) : Configuration string for the database
            SQLALCHEMY_DATABASE_URI
        dbname: (str) : The name of the database.
        superuser: (str : None) : name to grant privileges to
            if the database supports it.
    """

    if _is_sqlite(config):
        # sqlite does not use CREATE DATABASE
        return
    engine = create_engine(config)

    conn = engine.connect()
    conn.execute("COMMIT;")
    conn.execute(f"CREATE DATABASE {dbname};")

    conn.execute(f"GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {superuser};")
    conn.execute(f"ALTER ROLE {superuser} SUPERUSER;")

    conn.close()
    engine.dispose()


def drop_database(config, dbname):
    """drop_database

    Drops a database

    Default:
        drop_database(config, dbname, superuser=None)

    Note that if a superuser is included in the config, that user must have
    permissions to drop a database.

    Args:
        config: (str) : Configuration string for the database
            SQLALCHEMY_DATABASE_URI
        dbname: (str) : The name of the database.
    """

    if _is_sqlite(config):
        # sqlite does not use drop database
        if config.find("memory") == -1:
            filename = config[config.find("///") + 3 :]
            if os.path.exists(filename):
                os.remove(filename)
    else:
        engine = create_engine(config, poolclass=NullPool)

        conn = engine.connect()
        conn.execute("COMMIT")

        # close any existing connections
        # NOTE: break this out later
        if config.find("postgres") > -1:
            stmt = " ".join(
                [
                    "SELECT pg_terminate_backend(pid)",
                    "FROM pg_stat_activity WHERE datname = '{}'",
                ]
            ).format(dbname)

            conn.execute(stmt)

        result = conn.execute(f"DROP DATABASE IF EXISTS {dbname}")
        result.close()
        conn.close()
        engine.dispose()
