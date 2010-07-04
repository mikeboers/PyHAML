
import cgi
from itertools import chain


_attr_sort_order = {
    'id': -3,
    'class': -2,
    'http-equiv': -1, # for meta
    'checked': 1,
    'selected': 1,
}


class GeneratorSentinal(object):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
    def __repr__(self):
        if hasattr(self, 'name'):
            return '<Sentinal:%s>' % self.name
        return '<Sentinal at 0x%x>' % id(self)


class WhitespaceControlToken(str):
    def __repr__(self):
        return 'WhitespaceControlToken(%r)' % str.__repr__(self)


class BaseGenerator(object):
    
    indent_str = ''
    endl = ''
    endl_no_break = ''
    
    inc_depth = GeneratorSentinal(delta=1, name='inc_depth')
    dec_depth = GeneratorSentinal(delta=-1, name='dec_depth')
    _increment_tokens = (inc_depth, dec_depth)
    
    assert_newline = WhitespaceControlToken('assert_newline')
    lstrip = WhitespaceControlToken('lstrip')
    rstrip = WhitespaceControlToken('rstrip')
    
    def generate(self, node):
        return ''.join(self.generate_iter(node))
    
    def generate_iter(self, node):    
        generator = self._generate_string_tokens(node)
        buffer = []
        r_stripping = False
        try:
            while True:
                x = next(generator)
                if isinstance(x, WhitespaceControlToken):
                    if x == self.assert_newline:
                        if buffer and not buffer[-1].endswith('\n'):
                            buffer.append('\n')
                    elif x == self.lstrip:
                        # Work backwards through the buffer rstripping until
                        # we hit some non-white content. Then flush everything
                        # in the buffer upto that point. We need to leave the
                        # last one incase we get a "assert_newline" command.
                        for i in xrange(len(buffer) - 1, -1, -1):
                            buffer[i] = buffer[i].rstrip()
                            if buffer[i]:
                                for z in buffer[:i]:
                                    yield z
                                buffer = [buffer[i]]
                                break
                    elif x == self.rstrip:
                        r_stripping = True
                    else:
                        raise ValueError('unexpected WhitespaceControlToken %r' % x)
                else:
                    if r_stripping:
                        x = x.lstrip()
                        if x:
                            r_stripping = False
                    if x:
                        # Flush the buffer if we have non-white content as no
                        # lstrip command will get past this new token anyways.
                        if buffer and x.strip():
                            for y in buffer:
                                yield y
                            buffer = [x]
                        else:
                            buffer.append(x)
        except StopIteration:
            for x in buffer:
                yield x
    
    def _generate_string_tokens(self, node):
        self.depth = 0
        for token in self._visit_node(node):
            if token is None:
                continue
            if token in self._increment_tokens:
                self.depth += token.delta
            elif isinstance(token, basestring):
                if token:
                    yield token
            else:
                raise TypeError('unexpected token %r' % token)
        
    def _visit_node(self, node):
        for x in node.render_start(self) or []: yield x
        for child in node.children_to_render():
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
    
    indent_str = '\t'
    endl = '\n'
    endl_no_break = '\\\n'
    
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


