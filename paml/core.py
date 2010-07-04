
import re
import cgi

from . import nodes
from codegen import Compiler

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
    
    def process_string(self, source):
        for raw_line in source.splitlines():
            if raw_line.startswith('!'):
                self.add_node(nodes.Content(raw_line[1:]), depth=self.depth + 1)
                continue
            line = raw_line.lstrip()
            if not line:
                continue
            depth = len(raw_line) - len(line)
            while line:
                line = self.process_line(line, depth)
                depth += 1
    
    def process_line(self, line, depth):
        
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
        

def parse(source):
    parser = Parser()
    parser.process_string(source)
    return parser.root


    

if __name__ == '__main__':

    from mako.template import Template
    
    source = '''

    %head
        %title My test document.
    %body
        #header
            %img#logo(src='/img/logo.png')
            /
                # Navigation
                Another line of comments goes here.
            %ul#top-nav.nav
                %li Item 1
                %li Item 2
                %li Item 3
        #content
            %p
                The content goes in here.
                This is another line of the content.
            %p.warning.error(class_=class_)
                Paragraph 2.
        #footer %ul - for i in range(3): %li= i
        #id.class first
        .class#id second
        #test-id(key={}.get('value', 'default')) test
    <%def name="head()"></%def>
    '''

    print source
    print

    root = parse(source)

    def print_tree(node, depth=0):
        print '|   ' * depth + repr(node)
        for child in node.children:
            print_tree(child, depth + 1)

    print_tree(root)
    print
    print

    compiled = Compiler().render(root)
    print compiled
    
    template = Template(compiled)
    print template._code
    
    print template.render_unicode(class_='test')