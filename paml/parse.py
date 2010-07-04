
import re

from . import nodes


class Parser(object):
    
    def __init__(self):
        self.root = nodes.Document()
        self.stack = [(-1, self.root)]
    
    @property
    def depth(self):
        return self.stack[-1][0]
        
    @property
    def node(self):
        return self.stack[-1][1]
    
    def parse_string(self, source):
        self.parse(source.splitlines())
    
    def parse(self, source):
        for raw_line in source:
            if raw_line.startswith('!'):
                self.add_node(nodes.Content(raw_line[1:]), depth=self.depth + 1)
                continue
            line = raw_line.lstrip()
            if not line:
                continue
            depth = len(raw_line) - len(line)
            while line:
                line = self._parse_line(line, depth)
                depth += 1
    
    def _parse_line(self, line, depth):
        
        if line.startswith('/'):
            self.add_node(nodes.Comment(), depth=depth)
            return line[1:].lstrip()
        if line.startswith('='):
            self.add_node(nodes.Expression(line[1:].lstrip()), depth)
            return
        
        m = re.match(r'''
            (?:%(\w*))?  # tag name
            (            # id/class
              (?:\#[\w-]+|\.[\w-]+)+ 
            )?
        ''', line, re.X)
        if m and (m.group(1) is not None or m.group(2)):
            name, raw_id_class = m.groups()
            id, class_ = None, []
            for m2 in re.finditer(r'(#|\.)([\w-]+)', raw_id_class or ''):
                type, value = m2.groups()
                if type == '#':
                    id = value
                else:
                    class_.append(value)
               
            line = line[m.end():]
            
            attr_brace_deltas = {'(': 1, ')': -1}
            kwargs_expr_chars = []
            kwargs_expr_depth = 0
            pos = None
            for pos, char in enumerate(line):
                kwargs_expr_depth += attr_brace_deltas.get(char, 0)
                if not kwargs_expr_depth:
                    break
                kwargs_expr_chars.append(char)
            
            self.add_node(nodes.Tag(
                name,
                id,
                ' '.join(class_),
                ''.join(kwargs_expr_chars)[1:] # It will only have the first brace.
            ), depth=depth)  
            if kwargs_expr_chars:
                return line[pos + 1:].lstrip()
            else:
                return line.lstrip()

        
        m = re.match(r'''
            -
            \s*
            (for|if|while) # control type
            \s+
            (.+?):         # test
        ''', line, re.X)
        if m:
            self.add_node(nodes.Control(*m.groups()), depth=depth)
            return line[m.end():].lstrip()
               
        self.add_node(nodes.Content(line), depth=depth)
    
    def add_node(self, node, depth):
        while depth <= self.depth:
            self.stack.pop()
        self.node.children.append(node)
        self.stack.append((depth, node))
        

def parse_string(source):
    parser = Parser()
    parser.parse_string(source)
    return parser.root

    