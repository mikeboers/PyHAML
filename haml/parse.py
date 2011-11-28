
try:
    next
except NameError:
    from .backwards import next
import re

from . import nodes


class Parser(object):

    def __init__(self):
        self.root = nodes.Document()
        self._stack = [((-1, 0), self.root)]
        self._peek_line_buffer = None

    def parse_string(self, source):
        self.parse(source.splitlines())

    @property
    def _topmost_node(self):
        return self._stack[-1][1]

    def _next_line(self):
        """Get the next line."""
        if self._peek_line_buffer is not None:
            line = self._peek_line_buffer
            self._peek_line_buffer = None
            return line
        return next(self.source)

    def _peek_line(self):
        """Get the next line without consuming it."""
        if self._peek_line_buffer is None:
            self._peek_line_buffer = next(self.source)
        return self._peek_line_buffer

    def parse(self, source):
        self._parse_lines(source)
        self._parse_context(self.root)
    
    def _parse_lines(self, source):
        self.source = iter(source)
        indent_str = ''
        while True:
            try:
                raw_line = self._next_line()
            except StopIteration:
                break

            # Handle multiline statements.
            try:
                while raw_line.endswith('|'):
                    raw_line = raw_line[:-1]
                    if self._peek_line().endswith('|'):
                        raw_line += self._next_line()
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
            
            # Filter(Base) nodes recieve all content in their scope.
            if isinstance(self._topmost_node, nodes.FilterBase):
                self._topmost_node.add_line(indent_str, line)
                continue
            
            # Greedy nodes recieve all content in their scope.
            if isinstance(self._topmost_node, nodes.GreedyBase):
                self._add_node(
                    self._topmost_node.__class__(line),
                    (inter_depth, intra_depth)
                )
                continue
            
            # Discard all empty lines that are not in a greedy context.
            if not line:
                continue
            
            # Main loop. We process a series of tokens, which consist of either
            # nodes to add to the stack, or strings to be re-parsed and
            # attached as inline.
            last_line = None
            while line and line != last_line:
                last_line = line
                for token in self._parse_line(line):
                    if isinstance(token, nodes.Base):
                        self._add_node(token, (inter_depth, intra_depth))
                    elif isinstance(token, basestring):
                        line = token
                        intra_depth += 1
                    else:
                        raise TypeError('unknown token %r' % token)

    def _parse_line(self, line):

        # Escaping.
        if line.startswith('\\'):
            yield nodes.Content(line[1:].lstrip())
            return

        # HTML comments.
        m = re.match(r'/(\[if[^\]]+])?(.*)$', line)
        if m:
            yield nodes.HTMLComment(m.group(2).strip(), (m.group(1) or '').rstrip())
            return

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
            yield nodes.Expression(content, filters)
            return

        # SASS Mixins
        m = re.match(r'@(\w+)(?:\((.+?)\))?', line)
        if m:
            name, argspec = m.groups()
            yield nodes.MixinDef(name, argspec)
            yield line[m.end():].lstrip()
            return
        m = re.match(r'\+(\w+)(?:\((.+?)\))?', line)
        if m:
            name, argspec = m.groups()
            yield nodes.MixinCall(name, argspec)
            yield line[m.end():].lstrip()
            return

        # HAML Filters.
        m = re.match(r':(\w+)(?:\s+(.+))?$', line)
        if m:
            filter, content = m.groups()
            yield nodes.Filter(content, filter)
            return

        # HAML comments
        if line.startswith('-#'):
            yield nodes.HAMLComment(line[2:].lstrip())
            return  
        
        # XML Doctype
        if line.startswith('!!!'):
            yield nodes.Doctype(*line[3:].strip().split())
            return

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
            # Too bad I can't do this with a regex... *sigh*.
            brace_deltas = {'(': 1, ')': -1}
            brace_depth = 0
            pos = None
            for pos, char in enumerate(line):
                brace_depth += brace_deltas.get(char, 0)
                if not brace_depth:
                    break
            if pos: # This could be either None or 0 if it wasn't a brace.
                kwargs_expr = line[1:pos]
                line = line[pos + 1:]
            else:           
                kwargs_expr = None

            # Whitespace stripping
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
                name=name,
                id=id,
                class_=' '.join(class_),
                
                kwargs_expr=kwargs_expr,
                object_reference=object_reference,
                object_reference_prefix=object_reference_prefix, 
                self_closing=self_closing,
                strip_inner=strip_inner,
                strip_outer=strip_outer,
            )
            yield line
            return

        # Control statements.
        m = re.match(r'''
            -
            \s*
            (for|if|while|elif) # control type
            \s+
            (.+?):         # test
        ''', line, re.X)
        if m:
            yield nodes.Control(*m.groups())
            yield line[m.end():].lstrip()
            return
        m = re.match(r'-\s*else\s*:', line, re.X)
        if m:
            yield nodes.Control('else', None)
            yield line[m.end():].lstrip()
            return
        
        # Python source.
        if line.startswith('-'):
            if line.startswith('-!'):
                yield nodes.Python(line[2:].lstrip(), module=True)
            else:
                yield nodes.Python(line[1:].lstrip(), module=False)
            return

        # Content
        yield nodes.Content(line)

    def _prep_stack_for_depth(self, depth):  
        """Pop everything off the stack that is not shorter than the given depth."""
        while depth <= self._stack[-1][0]:
            self._stack.pop()

    def _add_node(self, node, depth):
        """Add a node to the graph, and the stack."""
        self._topmost_node.add_child(node, bool(depth[1]))
        self._stack.append((depth, node))
    
    def _parse_context(self, node):
        for child in node.children:
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
