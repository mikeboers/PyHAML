
from itertools import chain
import cgi
import collections
import re


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


class BaseGenerator(object):
    
    class no_strip(str):
        """A string class that will not have space removed."""
        def __repr__(self):
            return 'no_strip(%s)' % str.__repr__(self)
            
    indent_str = ''
    endl = ''
    endl_no_break = ''

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


def flatten_attr_list(input):
    if not input:
        return
    if isinstance(input, basestring):
        yield input
        return
    if not isinstance(input, collections.Iterable):
        yield input
        return
    for element in input:
        if element:
            for sub_element in flatten_attr_list(element):
                yield sub_element


def flatten_attr_dict(prefix_key, input):
    if not isinstance(input, dict):
        yield prefix_key, input
        return
    for key, value in input.iteritems():
        yield prefix_key + '-' + key, value


def camelcase_to_underscores(name):
    return re.sub(r'(?<!^)([A-Z])([A-Z]*)', lambda m: '_' + m.group(0), name).lower()


def _format_mako_attr_pair(k, v):
    if v is True:
        v = k
    return ' %s="%s"' % (k, cgi.escape(str(v)))


def mako_build_attr_str(*args, **kwargs):
    x = {}
    for arg in args:
        x.update(arg)
    obj_ref = kwargs.pop('__obj_ref', None)
    obj_ref_prefix = kwargs.pop('__obj_ref_pre', None)
    x.update(kwargs)
    x['id'] = flatten_attr_list(
        x.pop('id', [])
    )
    x['class'] = list(flatten_attr_list(
        [x.pop('class', []), x.pop('class_', [])]
    ))
    if obj_ref:
        class_name = camelcase_to_underscores(obj_ref.__class__.__name__)
        x['id'] = filter(None, [obj_ref_prefix, class_name, getattr(obj_ref, 'id', None)])
        x['class'].append((obj_ref_prefix + '_' if obj_ref_prefix else '') + class_name)
    x['id'] = '_'.join(map(str, x['id']))
    x['class'] = ' '.join(map(str, x['class']))
    pairs = []
    for k, v in x.iteritems():
        pairs.extend(flatten_attr_dict(k, v))
    pairs.sort(key=lambda pair: (_attr_sort_order.get(pair[0], 0), pair[0]))
    return ''.join(_format_mako_attr_pair(k, v) for k, v in pairs if v)


def generate_mako(node):
    return MakoGenerator().generate(node)
