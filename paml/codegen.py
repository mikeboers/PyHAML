
import cgi
from itertools import chain


_attr_sort_order = {
    'id': -3,
    'class': -2,
    'http-equiv': -1, # for meta
    'checked': 1,
    'selected': 1,
}


class _GeneratorSentinal(object):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)



class BaseGenerator(object):
    
    inc_depth = _GeneratorSentinal(delta=1)
    dec_depth = _GeneratorSentinal(delta=-1)
    _increment_tokens = (inc_depth, dec_depth)
    
    assert_newline = _GeneratorSentinal()
    
    no_whitespace = _GeneratorSentinal(
        indent_str = '',
        endl = '',
        endl_no_break = '',
    )
    default_whitespace = no_whitespace
    _whitespace_tokens = (no_whitespace, default_whitespace)
    
    pop_whitespace = _GeneratorSentinal()
    
    
    def __init__(self):
        self.whitespace_stack = [self.default_whitespace]
    
    def __getattr__(self, name):
        return getattr(self.whitespace_stack[-1], name)
    
    def generate(self, node):
        self.depth = 0
        result = []
        for token in self._visit_node(node):
            if token is None:
                continue
            if token in self._increment_tokens:
                self.depth += token.delta
            elif token in self._whitespace_tokens:
                self.whitespace_stack.append(token)
            elif token is self.pop_whitespace:
                self.whitespace_stack.pop()
            elif token is self.assert_newline:
                if result and result[-1][-1] != '\n':
                    result.append('\n')
            elif isinstance(token, basestring):
                if token:
                    result.append(token)
            else:
                raise TypeError('unexpected token %r' % token)
        return ''.join(result)
        
    def _visit_node(self, node):
        for x in node.render_start(self) or []: yield x
        for child in node.children:
            for x in self._visit_node(child): yield x
        for x in node.render_end(self) or []: yield x
    
    def indent(self, delta=0):
        return self.indent_str * (self.depth + delta)
    
    def _set_whitespace_from_token(self, token):
        self.__dict__.update(token.__dict__)
    
    def noop(self):
        return None
    
    start_document = noop


class MakoGenerator(BaseGenerator):
    
    default_whitespace = _GeneratorSentinal(
        indent_str = '\t',
        endl = '\n',
        endl_no_break = '\\\n',
    )
    
    def start_document(self):
        return (
            '<%%! from %s import mako_build_attr_str as __P_attrs %%>' % __name__ +
            self.endl_no_break
        )

        
def mako_build_attr_str(*args, **kwargs):
    x = {}
    for arg in args:
        x.update(arg)
    x.update(kwargs)
    pairs = x.items()
    pairs.sort(key=lambda pair: (_attr_sort_order.get(pair[0], 0), pair[0]))
    return ''.join(' %s="%s"' % (k.strip('_'), cgi.escape(v)) for k, v in pairs)


def generate_mako(node):
    return MakoGenerator().generate(node)


