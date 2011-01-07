
from .parse import parse_string
from .codegen import generate_mako

def preprocessor(source):
    return generate_mako(parse_string(source))
