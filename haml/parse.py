
import re

from . import nodes


class Parser(object):
    
    def __init__(self):
        self.root = nodes.Document()
        self.stack = [((-1, 0), self.root)]
        self._peeked = None
    
    @property
    def depth(self):
        return self.stack[-1][0]
        
    @property
    def node(self):
        return self.stack[-1][1]
    
    def parse_string(self, source):
        self.parse(source.splitlines())
    
    def next_line(self):
        if self._peeked is not None:
            line = self._peeked
            self._peeked = None
            return line
        return next(self.source)
    
    def peek_line(self):
        if self._peeked is None:
            self._peeked = next(self.source)
        return self._peeked
    
    def parse(self, source):
        self.source = iter(source)
        while True:
            try:
                raw_line = self.next_line()
            except StopIteration:
                return
            try:
                while raw_line.endswith('|'):
                    raw_line = raw_line[:-1]
                    if self.peek_line().endswith('|'):
                        raw_line += self.next_line()
            except StopIteration:
                pass
            line = raw_line.lstrip()
            if not line:
                continue
            # We track the inter-line depth seperate from the intra-line depth
            # so that indentation due to whitespace always results in more
            # depth in the graph than many nested nodes from a single line.
            inter_depth = len(raw_line) - len(line)
            intra_depth = 0
            # Cleanup the stack. We should only need to do this here as the
            # depth only goes up until it is calculated from the next line.
            self.prep_stack_for_depth((inter_depth, 0))
            last_line = None
            while line and line != last_line:
                last_line = line
                for token in self._parse_line(line):
                    if isinstance(token, nodes.Base):
                        self.add_node(token, (inter_depth, intra_depth))
                    elif isinstance(token, basestring):
                        line = token
                        intra_depth += 1
                    else:
                        raise TypeError('unknown token type %r' % token)
                
    
    def _parse_line(self, line):
        
        if isinstance(self.node, nodes.GreedyBase):
            yield self.node.__class__.with_parent(self.node, line)
            return
        
        # Escape a line so it doesn't get touched.
        if line.startswith('\\'):
            yield nodes.Content(line[1:].lstrip())
            return
        
        # HTML comments.
        m = re.match(r'/(\[if[^\]]+])?(.*)$', line)
        if m:
            yield nodes.Comment(m.group(2).strip(), (m.group(1) or '').rstrip())
            return
        
        # Expressions.
        m = re.match(r'''
            (&?)
            =
            (?:\|(\w+(?:,\w+)*))?
            \s*
            (.*)
            $        
        ''', line, re.X)
        if m:
            add_escape, filters, content = m.groups()
            filters = filters or ''
            if add_escape:
                filters = filters + (',' if filters else '') + 'h'
            yield nodes.Expression(content, filters)
            return
        
        # Filters
        m = re.match(r':(\w+)(?:\s+(.+))?$', line)
        if m:
            filter, content = m.groups()
            yield nodes.Filtered(content, filter)
            return
        
        # Silent comments
        if line.startswith('-#'):
            yield nodes.Silent(line[2:].lstrip())
            return
        
        # Tags.
        m = re.match(r'''
            (?:%(%?\w*))?  # tag name. the extra % is for mako
            (              # id/class
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
            
            # Extract the kwargs expression.
            attr_brace_deltas = {'(': 1, ')': -1}
            kwargs_expr_chars = []
            kwargs_expr_depth = 0
            pos = None
            for pos, char in enumerate(line):
                kwargs_expr_depth += attr_brace_deltas.get(char, 0)
                if not kwargs_expr_depth:
                    break
                kwargs_expr_chars.append(char)
            if kwargs_expr_chars:
                line = line[pos + 1:]
            else:
                line = line
            
            # Whitespace striping
            m2 = re.match(r'([<>]+)', line)
            strip_outer = strip_inner = False
            if m2:
                strip_outer = '>' in m2.group(1)
                strip_inner = '<' in m2.group(1)
                line = line[m2.end():]
                 
            # Self closing tags
            self_closing = bool(line and line[0] == '/')
            line = line[int(self_closing):].lstrip()
                
            yield nodes.Tag(
                name,
                id,
                ' '.join(class_),
                ''.join(kwargs_expr_chars)[1:], # It will only have the first brace.
                self_closing,
                strip_outer=strip_outer,
                strip_inner=strip_inner,
            )
            yield line
            return
            
            tokens = list(self._parse_line(line))
            if len(tokens) == 1 and isinstance(tokens[0], (nodes.Content, nodes.Expression)):
                tag.inline_child = tokens[0]
            else:
                for x in tokens:
                    yield x
            return

        # Control statements.
        m = re.match(r'''
            -
            \s*
            (for|if|while) # control type
            \s+
            (.+?):         # test
        ''', line, re.X)
        if m:
            yield nodes.Control(*m.groups())
            yield line[m.end():].lstrip()
            return
        
        # Python source.
        if line.startswith('-'):
            if line.startswith('-!'):
                yield nodes.Source(line[2:].lstrip(), module=True)
            else:
                yield nodes.Source(line[1:].lstrip(), module=False)
            return
        
        # Content
        yield nodes.Content(line)
        
    def prep_stack_for_depth(self, depth):        
        while depth <= self.depth:
            self.stack.pop()
                
    def add_node(self, node, depth):
        self.node.add_child(node, bool(depth[1]))
        self.stack.append((depth, node))
        

def parse_string(source):
    parser = Parser()
    parser.parse_string(source)
    return parser.root

    