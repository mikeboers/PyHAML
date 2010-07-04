
from . import codegen
from .parse import Parser
from . import codegen

def parse_string(source):
    parser = Parser()
    parser.process_string(source)
    return parser.root

def generate_mako(node):
    return codegen.MakoGenerator().render(node)