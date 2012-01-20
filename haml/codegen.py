
from itertools import chain
import cgi
import collections
import re


from . import runtime


class GeneratorSentinal(object):
    
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        
    def __repr__(self):
        if hasattr(self, 'name'):
            return '<Sentinal:%s>' % self.name
        return '<Sentinal at 0x%x>' % id(self)


class Generator(object):
    
    class no_strip(str):
        """A string class that will not have space removed."""
        def __repr__(self):
            return 'no_strip(%s)' % str.__repr__(self)
    
    indent_str = '\t'
    endl = '\n'
    endl_no_break = '\\\n'

    inc_depth = GeneratorSentinal(delta=1, name='inc_depth')
    dec_depth = GeneratorSentinal(delta=-1, name='dec_depth')
    _increment_tokens = (inc_depth, dec_depth)

    line_continuation = no_strip('\\\n')
    lstrip = GeneratorSentinal(name='lstrip')
    rstrip = GeneratorSentinal(name='rstrip')

    def generate(self, node):
        return ''.join(self.generate_iter(node))

    def generate_iter(self, node):
        buffer = []
        r_stripping = False
        self.depth = 0
        self.node_data = {}
        for token in node.render(self):
            if isinstance(token, GeneratorSentinal):
                if token in self._increment_tokens:
                    self.depth += token.delta
                elif token is self.lstrip:
                    # Work backwards through the buffer rstripping until
                    # we hit some non-white content. Then flush everything
                    # in the buffer upto that point. We need to leave the
                    # last one incase we get a "line_continuation" command.
                    # Remember that no_strip strings are simply ignored.
                    for i in xrange(len(buffer) - 1, -1, -1):
                        if isinstance(buffer[i], self.no_strip):
                            continue
                        buffer[i] = buffer[i].rstrip()
                        if buffer[i]:
                            for x in buffer[:i]:
                                yield x
                            buffer = buffer[i:]
                            break
                elif token is self.rstrip:
                    r_stripping = True
                else:
                    raise ValueError('unexpected %r' % token)
            elif isinstance(token, basestring):
                # If we have encountered an rstrip token in the past, then
                # we are removing all leading whitespace on incoming tokens.
                # We must completely ignore no_strip strings as they go by.
                if r_stripping:
                    if not isinstance(token, self.no_strip):
                        token = token.lstrip()
                        if token:
                            r_stripping = False
                if token:
                    # Flush the buffer if we have non-white content as no
                    # lstrip command will get past this new token anyways.
                    if buffer and token.strip() and not isinstance(token, self.no_strip):
                        for x in buffer:
                            yield x
                        buffer = [token]
                    else:
                        buffer.append(token)
            else:
                raise ValueError('unknown token %r' % token)
        for x in buffer:
            yield x

    def indent(self, delta=0):
        return self.indent_str * (self.depth + delta)

    def start_document(self):
        return (
            '<%%! from %s import runtime as __HAML %%>' % __package__ +
            self.endl_no_break
        )







    


def generate_mako(node):
    return Generator().generate(node)
