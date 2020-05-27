# dbbase/column_types.py
"""
This module implement subclassed column types.
"""
from sqlalchemy import Column


class WriteOnlyColumn(Column):
    """
    This class creates a subclassed column that identifies it as write only.

    The use case for it derives from the need to screen out columns
    such as passwords from user tables.

    """

    info = {"writeOnly": True}
