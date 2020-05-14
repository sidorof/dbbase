# doc_utils.py
"""
This module supports documenting tables with helper functions.
"""
from copy import deepcopy
from sqlalchemy.sql import functions
from sqlalchemy.sql import elements


def _default(value):
    """_default in more readable form"""
    key = "default"
    if value is None:
        return {key: None}

    ddict = deepcopy(value.__dict__)

    # remove unwanted keys
    if "dispatch" in ddict:
        ddict.pop("dispatch")

    if "column" in ddict:
        ddict.pop("column")

    if isinstance(ddict["arg"], elements.TextClause):
        # ex. server_default=db.text("0") -- place a number
        ddict["arg"] = f'db.text("{ddict["arg"].text}")'

    elif callable(ddict["arg"]):
        # local function
        ddict["arg"] = ddict["arg"].__qualname__

    elif isinstance(ddict["arg"], functions.GenericFunction):
        # hopefully just server functions
        # trying to get to ex: db.func.now()
        name = str(ddict["arg"].__class__)
        name = name[name.find("<class '") + 8: name.find('>') - 1]

        ddict["arg"] = f"db.func.{name.split('.')[-1]}()"

    else:
        # leave it alone
        pass

    return {key: ddict}


def _onupdate(value):
    """ _onupdate

    This function marks the default as on update.
    """
    res = _default(value)
    if res['default'] is not None:
        return {"onupdate": res["default"]}

    return res


def _server_default(value):
    """ _server_default

    This function marks the default as server_default

    """
    res = _default(value)
    if res['default'] is not None:
        return {"server_default": res["default"]}

    return res


def _server_onupdate(value):
    """ _server_onupdate

    This function marks the default as _server_onupdate

    """
    res = _default(value)
    if res['default'] is not None:
        return {"server_onupdate": res["default"]}

    return res


def _foreign_keys(value):
    """_foreign_keys

    key name is changed to foreign_key
    """
    key = "foreign_key"

    if value:
        foreign_keys = []
        for col in value:
            foreign_keys.append(col.target_fullname)

        if len(foreign_keys) > 1:
            return {key: foreign_keys}

        return {key: foreign_keys[0]}

    return None


def _only_if_true(value):
    """ _only_if_true

    Returns either (None, True) or (None, None)
    """
    if value is False:
        value = None
    return None, value


def _type(value):
    """ _type

    Depending on the type, might send back a dict
    rather than the standard tuple. This is to account for situations like:

    {
        "type": "integer",
        "format": "int32",
    }

    rather than:

    ("type", "string")

    """
    val_str = str(value)
    if str(value).endswith("[]"):
        # an array
        res = {"type": "array", "zero-indexes": value.zero_indexes}
        items = {}
        if value.dimensions:
            items["dimensions"] = value.dimensions

        res["items"] = _type(value.item_type)

    elif val_str == "INTEGER":
        res = {
            "type": "integer",
            "format": "int32",
        }
    elif val_str == "SMALLINT":
        res = {
            "type": "integer",
            "format": "int8",
        }
    elif val_str == "BIGINT":
        res = {
            "type": "integer",
            "format": "int64",
        }
    elif val_str == "DATETIME":
        res = {"type": "date-time"}

    elif val_str.startswith("VARCHAR"):
        # no support for minimum length right now
        pos1 = val_str.find("(")
        if val_str == "VARCHAR":
            res = {"type": "string"}
        elif pos1 > -1:
            res = {"type": "string", "maxLength": int(val_str[pos1 + 1: -1])}
        else:
            res = {"type": val_str}
    else:
        res = {"type": val_str.lower()}

    if hasattr(value, "choices"):
        res.update(dict(choices=value.choices))

    return res


EXPRESSION_KEYS = {
    "type": _type,
    "primary_key": _only_if_true,
    "nullable": None,
    "default": _default,
    "onupdate": _onupdate,
    "server_default": _server_default,
    "server_onupdate": _server_onupdate,
    "index": None,
    "unique": _only_if_true,
    "system": _only_if_true,
    "doc": None,
    "foreign_keys": _foreign_keys,
    "comment": None,
    "info": None,
}


def process_expression(expression):
    """
    This function uses the dict from expression and converts selected elements
    for documentation.
    """
    doc_dict = {}
    for key, func in EXPRESSION_KEYS.items():
        expr_value = getattr(expression, key)
        if expr_value is not None:
            if func is not None:
                item = func(expr_value)
                if isinstance(item, tuple):
                    if item[1] is not None:
                        if item[0] is None:
                            doc_dict[key] = item[1]
                        else:
                            doc_dict[item[0]] = item[1]

                elif isinstance(item, dict):
                    doc_dict.update(item)
                elif item is None:
                    # skip it
                    pass
                elif item == (None, None):
                    # skip
                    pass
                else:
                    # should not here, but here we are
                    raise ValueError("unknown type")
            else:
                doc_dict[key] = expr_value

    return doc_dict
