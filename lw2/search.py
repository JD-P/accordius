import json
import re
from django.db.models import Q 

"""Search Syntax Quick Guide

A search string is made up of one or more EXPRESSIONS which are joined by 
OPERATORS. 

- An expression is a string of non-whitespace unicode characters which may or 
  may not be enclosed by quotation marks. 

- An expression enclosed in DOUBLE QUOTES is searched for exactly, otherwise 
  it's searched for as a substring and may have enhancement features such as 
  synonym matching applied.

- There are three operators: AND, OR, and NOT

- The AND operator is applied by separating two or more expressions with SPACES.

- The OR operator is applied by typing capital OR surrounded by whitespace 
  between two or more expressions. (Not currently implemented)

- The NOT operator is applied by putting a dash (-) in front of an expression,
  this will cause the search backend to use an exclude() instead of a filter()
  for that exrpression. (TODO: Make this actually work, currently just AND)

The syntax also supports PARAMETERS, which are special search string keywords
that can be passed to specify certain behavior such as date restrictions. These
are structured as keyword:argument pairs that may appear as expressions in a
search string. All parameters are currently undefined, but in a later edition
will provide extended search functionality."""

def parse_search_string(search_s):
    # Extract parameters
    parameters = {}
    param_re = re.compile("(\S+):(\S+)")
    parameters_raw = param_re.findall(search_s)
    for parameter in parameters_raw:
        parameters[parameter[0]] = parameter[1]
    search_s = param_re.sub('', search_s)
    # Extract OR operations
    or_op_re = re.compile("(\S+) OR (\S+)")
    or_ops = or_op_re.findall(search_s)
    search_s = or_op_re.sub('', search_s)
    # Extract rest
    and_ops = search_s.split()
    return {"parameters":parameters,
            "or_ops":or_ops,
            "and_ops":and_ops}

def mk_search_filters(parsed_operations):
    """Create the search filters that implement the operations from the parsed
    query string."""
    filters = []
    for and_op in parsed_operations["and_ops"]:
        operation = mk_operation(and_op)
        operation["type"] = "and"
        filters.append(operation)
    for or_op in parsed_operations["or_ops"]:
        operation = {"type":"or",
                     "exclude":None,
                     "Q":None}
        left_or = mk_operation(or_op[0])
        right_or = mk_operation(or_op[1])
        operation["Q"] = (left_or["Q"] | right_or["Q"])
        filters.append(operation)
    return filters

def mk_operation(op):
    operation = {"exclude":False,
                     "Q":None}
    if op[0] == "-":
        operation["exclude"] = True
        op = op[1:]
        
    if op[0] == op[-1] == "\"":
        operation["Q"] = Q(body__iexact=op)
    else:
        operation["Q"] = Q(body__icontains=op)
    return operation
