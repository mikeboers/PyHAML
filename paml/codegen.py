
import cgi


_attr_sort_order = {
    'id': -2,
    'class': -1,
    'checked': 1,
    'selected': 1,
}


class BaseGenerator(object):
    
    indent_str = '\t'
    
    def generate(self, node):
        return ''.join(self._generate_iter(node))
        
    def _generate_iter(self, node):
        for depth, line in self._visit_node(node):
            if line is not None:
                yield (depth - 1) * self.indent_str + line + '\n'
    
    def _visit_node(self, node):
        yield 0, node.render_start(self)
        for line in node.render_content(self):
            yield 1, line
        for child in node.children:
            for depth, x in self._visit_node(child):
                yield depth + 1, x
        yield 0, node.render_end(self)
    
    def noop(self):
        return None
    
    start_document = noop


class MakoGenerator(BaseGenerator):
    
    def start_document(self):
        return '<%%! from %s import mako_build_attr_str as __P_attrs %%>\\' % __name__

        
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


