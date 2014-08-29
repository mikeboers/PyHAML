import itertools
import re
import tokenize

from six import string_types, next

from . import nodes


def split_balanced_parens(line, depth=0):
    # Too bad I can't do this with a regex... *sigh*.
    deltas = {'(': 1, ')': -1}
    pos = None
    for pos, char in enumerate(line):
        depth += deltas.get(char, 0)
        if not depth:
            break
    if pos: # This could be either None or 0 if it wasn't a brace.
        return line[:pos+1], line[pos+1:]
    else:           
        return '', line
    
    
class Parser(object):

    def __init__(self):
        self.root = nodes.Document()
        self._stack = [((-1, 0), self.root)]

    def parse_string(self, source):
        self.parse(source.splitlines())

    @property
    def _topmost_node(self):
        return self._stack[-1][1]

    def _peek_buffer(self, i=0):
        """Get the next line without consuming it."""
        while len(self._buffer) <= i:
            self._buffer.append(next(self._source))
        return self._buffer[i]

    def _consume_buffer(self):
        """Get the next line."""
        if self._buffer:
            return self._buffer.pop(0)

    def _replace_buffer(self, line):
        """Replace the contents of the first line in the buffer with the given."""
        self._buffer[0] = line

    def _make_readline_peeker(self):
        """Make a readline-like function which peeks into the source."""
        counter = itertools.count(0)
        def readline():
            try:
                return self._peek_buffer(next(counter))
            except StopIteration:
                return ''
        return readline

    def _peek_python_tokens(self):
        """Return a generator of Python tokens from the source.

        Does not consume any of the source.

        """
        return tokenize.generate_tokens(self._make_readline_peeker())

    def _consume_python_token(self, token):
        """Consume the buffer up to the given token (from _peek_python_tokens).

        Returns a single string that was consumed.

        """
        ret = []
        line, col = token[3]
        if line > 1:
            ret = self._buffer[:line-1]
            self._buffer[:line-1] = []
        ret.append(self._buffer[0][:col])
        self._buffer[0] = self._buffer[0][col:]
        return ''.join(ret)

    def _match_python_expr(self, first=None, last=None):
        openers = set('({[')
        closers = set(')}]')
        close_to_open = {')': '(', '}': '{', ']': '['}
        stack = []
        try:
            for token_i, token in enumerate(self._peek_python_tokens()):
                type_, value, _, _, _  = token

                if not token_i and first is not None:
                    if value not in first:
                        return

                if type_ == tokenize.OP:
                    if value in openers:
                        stack.append(token[1])
                    elif value in closers:
                        if stack[-1] != close_to_open[value]:
                            # Mismatched brackets!
                            return
                        stack.pop(-1)

                if not stack and (last is None or value in last):
                    return self._consume_python_token(token)

        except IndentationError:
            return

    def parse(self, source):
        self._source = iter(source)
        self._buffer = []
        self._parse_buffer()
        self._parse_context(self.root)
    
    def _parse_buffer(self):
        indent_str = ''
        raw_line = None
        while True:

            if raw_line is not None:
                self._consume_buffer()

            try:
                raw_line = self._peek_buffer()
            except StopIteration:
                break

            # Handle multiline statements.
            try:
                while raw_line.endswith('|'):
                    raw_line = raw_line[:-1]
                    if self._peek_buffer(1).endswith('|'):
                        self._consume_buffer()
                        raw_line += self._peek_buffer()
            except StopIteration:
                pass

            line = raw_line.lstrip()
            
            if line:
                
                # We track the inter-line depth seperate from the intra-line depth
                # so that indentation due to whitespace always results in more
                # depth in the graph than many nested nodes from a single line.
                inter_depth = len(raw_line) - len(line)
                intra_depth = 0

                indent_str = raw_line[:inter_depth]
                
                # Cleanup the stack. We should only need to do this here as the
                # depth only goes up until it is calculated from the next line.
                self._prep_stack_for_depth((inter_depth, intra_depth))
                
            else:
                
                # Pretend that a blank line is at the same depth as the
                # previous.
                inter_depth, intra_depth = self._stack[-1][0]
            
            # Filter(Base) nodes receive all content in their scope.
            if isinstance(self._topmost_node, nodes.FilterBase):
                self._topmost_node.add_line(indent_str, line)
                continue
            
            # Greedy nodes receive all content in their scope.
            if isinstance(self._topmost_node, nodes.GreedyBase):
                self._add_node(
                    self._topmost_node.__class__(line),
                    (inter_depth, intra_depth)
                )
                continue
            
            # Discard all empty lines that are not in a greedy context.
            if not line:
                continue
            
            # Main loop. We continue removing statements from the front of the
            # line until the line has been exhausted. We keep the buffer
            # accurate so that the Python tokenize functions will work.
            while line:
                self._replace_buffer(line)
                node, line = self._parse_statement()
                self._add_node(node, (inter_depth, intra_depth))
                line = line.lstrip()
                intra_depth += 1


    def _parse_statement(self):

        line = self._peek_buffer()

        # Escaping.
        if line.startswith('\\'):
            return (
                nodes.Content(line[1:]),
                ''
            )

        # HTML comments.
        m = re.match(r'/(\[if[^\]]+])?(.*)$', line)
        if m:
            return (
                nodes.HTMLComment(m.group(2).strip(), (m.group(1) or '').rstrip()),
                ''
            )

        # Expressions.
        m = re.match(r'''
            (&?)                  # HTML escaping flag
            =
            (?:\|(\w+(?:,\w+)*))? # mako filters
            \s*
            (.*)                  # expression content
            $
        ''', line, re.X)
        if m:
            add_escape, filters, content = m.groups()
            filters = filters or ''
            if add_escape:
                filters = filters + (',' if filters else '') + 'h'
            return (
                nodes.Expression(content, filters),
                ''
            )

        # SASS Mixins
        m = re.match(r'@(\w+)', line)
        if m:
            name = m.group(1)
            line = line[m.end():]
            self._replace_buffer(line)
            argspec = self._match_python_expr(first=set('('), last=set(')'))
            if argspec:
                argspec = argspec[1:-1]
                line = self._peek_buffer()
            return (
                nodes.MixinDef(name, argspec),
                line
            )

        m = re.match(r'\+([\w.]+)', line)
        if m:
            name = m.group(1)
            line = line[m.end():]
            self._replace_buffer(line)
            argspec = self._match_python_expr(first=set('('), last=set(')'))
            if argspec:
                argspec = argspec[1:-1]
                line = self._peek_buffer()
            return (
                nodes.MixinCall(name, argspec),
                line
            )

        # HAML Filters.
        m = re.match(r':(\w+)(?:\s+(.+))?$', line)
        if m:
            filter, content = m.groups()
            return (
                nodes.Filter(content, filter),
                ''
            )

        # HAML comments
        if line.startswith('-#'):
            return (
                nodes.HAMLComment(line[2:].lstrip()),
                ''
            ) 
        
        # XML Doctype
        if line.startswith('!!!'):
            return (
                nodes.Doctype(*line[3:].strip().split()),
                ''
            )

        # Tags.
        m = re.match(r'''
            (?:%(%?(?:\w+:)?[\w-]*))? # tag name. the extra % is for mako
            (?:
              \[(.+?)(?:,(.+?))?\]    # object reference and prefix
            )? 
            (                         
              (?:\#[\w-]+|\.[\w-]+)+  # id/class
            )?
        ''', line, re.X)                                
        # The match only counts if we have a tag name or id/class.
        if m and (m.group(1) is not None or m.group(4)):
            name, object_reference, object_reference_prefix, raw_id_class = m.groups()
            
            # Extract id value and class list.
            id, class_ = None, []
            for m2 in re.finditer(r'(#|\.)([\w-]+)', raw_id_class or ''):
                type, value = m2.groups()
                if type == '#':
                    id = value
                else:
                    class_.append(value)
            line = line[m.end():]

            # Extract the kwargs expression.
            self._replace_buffer(line)
            kwargs_expr = self._match_python_expr(first=set('('), last=set(')'))
            if kwargs_expr:
                kwargs_expr = kwargs_expr[1:-1]
                line = self._peek_buffer()

            # Whitespace stripping
            m2 = re.match(r'([<>]+)', line)
            strip_outer = strip_inner = False
            if m2:
                strip_outer = '>' in m2.group(1)
                strip_inner = '<' in m2.group(1)
                line = line[m2.end():]

            # Self-closing tags
            self_closing = bool(line and line[0] == '/')
            line = line[int(self_closing):].lstrip()

            return (
                nodes.Tag(
                    name=name,
                    id=id,
                    class_=' '.join(class_),
                    
                    kwargs_expr=kwargs_expr,
                    object_reference=object_reference,
                    object_reference_prefix=object_reference_prefix, 
                    self_closing=self_closing,
                    strip_inner=strip_inner,
                    strip_outer=strip_outer,
                ),
                line
            )

        # Control statements.
        m = re.match(r'''
            -
            \s*
            (for|if|while|elif) # control type
        ''', line, re.X)
        if m:
            control_type = m.group(1)
            self._replace_buffer(line[m.end():].lstrip())
            expr = self._match_python_expr(last=set(':'))
            return (
                nodes.Control(control_type, expr[:-1]),
                self._peek_buffer()
            )
        m = re.match(r'-\s*else\s*:', line, re.X)
        if m:
            return (
                nodes.Control('else', None),
                line[m.end():].lstrip()
            )
        
        # Python source.
        if line.startswith('-'):
            if line.startswith('-!'):
                return (
                    nodes.Python(line[2:].lstrip(), module=True),
                    ''
                )
            else:
                return (
                    nodes.Python(line[1:].lstrip(), module=False),
                    ''
                )

        # Content
        return (
            nodes.Content(line),
            ''
        )

    def _prep_stack_for_depth(self, depth):  
        """Pop everything off the stack that is not shorter than the given depth."""
        while depth <= self._stack[-1][0]:
            self._stack.pop()

    def _add_node(self, node, depth):
        """Add a node to the graph, and the stack."""
        self._topmost_node.add_child(node, bool(depth[1]))
        self._stack.append((depth, node))
    
    def _parse_context(self, node):
        for child in node.iter_all_children():
            self._parse_context(child)
        i = 0
        while i < len(node.children) - 1:
            if node.children[i].consume_sibling(node.children[i + 1]):
                del node.children[i + 1]
            else:
                i += 1


def parse_string(source):
    """Parse a string into a HAML node to be compiled."""
    parser = Parser()
    parser.parse_string(source)
    return parser.root
