            
import cgi
from itertools import chain

class Base(object):
    
    def __init__(self):
        self.children = []
        self.inline_child = None
    
    def add_child(self, node, inline):
        if inline:
            self.inline_child = node
        else:
            self.children.append(node)
    
    def render_start(self, engine):
        return None
    
    def render_content(self, engine):
        if self.inline_child:
            return chain(
                self.inline_child.render_start(engine),
                self.inline_child.render_content(engine),
                self.inline_child.render_end(engine),
            )
        return []
    
    def children_to_render(self):
        return self.children
    
    def render_end(self, engine):
        return None
    
    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))


class GreedyBase(Base):
    
    @classmethod
    def with_parent(cls, parent, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj._parent = parent
        return obj
    
    @property
    def parent(self):
        return getattr(self, '_parent', None)
    
    @property
    def outermost_node(self):
        x = self
        while x.parent is not None:
            x = x.parent
        return x
    
    @property
    def depth_attr(self):
        return '_%s_depth' % self.__class__.__name__
    
    def get_depth(self, engine):
        return getattr(engine, self.depth_attr, 0)
    
    def inc_depth(self, engine):
        depth = getattr(engine, self.depth_attr, 0)
        setattr(engine, self.depth_attr, depth + 1)
        return depth
    
    def dec_depth(self, engine):
        depth = getattr(engine, self.depth_attr) - 1
        setattr(engine, self.depth_attr, depth)
        return depth


class Document(Base):
    
    def render_start(self, engine):
        yield engine.start_document()


class Content(Base):
    
    def __init__(self, content):
        super(Content, self).__init__()
        self.content = content
    
    def render_start(self, engine):
        yield engine.indent()
        yield self.content
        yield engine.endl
        yield engine.inc_depth
    
    def render_end(self, engine):
        yield engine.dec_depth
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.content)


class Expression(Content, GreedyBase):
    
    def __init__(self, content, filters=''):
        super(Expression, self).__init__(content)
        self.filters = filters
    
    def render_start(self, engine):
        if self.content.strip():
            yield engine.indent()
            filters = self.outermost_node.filters
            yield '${%s%s}' % (self.content.strip(), ('|' + filters if filters else ''))
            yield engine.endl
        yield engine.inc_depth # This is countered by the Content.render_end
    
    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.content, self.filters)
        
    


class Tag(Base):
    
    self_closing_names = set('''
        br
        hr
        img
        input
        link
        meta
    '''.strip().split())
    
    def __init__(self, name, id, class_, kwargs_expr=None, self_closing=False,
        strip_inner=False, strip_outer=False):
        
        super(Tag, self).__init__()
        
        self.name = (name or 'div').lower()
        self.id = id
        self.class_ = (class_ or '').replace('.', ' ').strip()
        self.kwargs_expr = kwargs_expr
        self.self_closing = self_closing
        self.strip_inner = strip_inner
        self.strip_outer = strip_outer
    
    def render_start(self, engine):
        
        const_attrs = {}
        if self.id:
            const_attrs['id'] = self.id
        if self.class_:
            const_attrs['class'] = self.class_
        
        if not self.kwargs_expr:
            attr_str = ''.join(' %s="%s"' % (k, cgi.escape(v)) for k, v in const_attrs.items())
        elif not const_attrs:
            attr_str = '<%% __M_writer(__P_attrs(%s)) %%>' % self.kwargs_expr
        else:
            attr_str = '<%% __M_writer(__P_attrs(%r, %s)) %%>' % (const_attrs, self.kwargs_expr)
        
        if self.strip_outer:
            yield engine.lstrip
        else:
            yield engine.indent()
        
        if self.self_closing or self.name in self.self_closing_names:
            yield '<%s%s />' % (self.name, attr_str)
            if self.strip_outer:
                yield engine.rstrip
            else:
                yield engine.endl
        else:
            yield '<%s%s>' % (self.name, attr_str)
            if self.children:
                if self.strip_inner:
                    yield engine.rstrip
                else:
                    yield engine.endl
                    yield engine.inc_depth
    
    def render_content(self, engine):
        if self.inline_child:
            return chain(
                [engine.rstrip],
                super(Tag, self).render_content(engine),
                [engine.lstrip],
            )
    
    def render_end(self, engine):
        if self.strip_inner:
            yield engine.lstrip
        if not (self.self_closing or self.name in self.self_closing_names):
            if self.children:
                yield engine.dec_depth
                yield engine.indent()
            yield '</%s>' % self.name
            if self.strip_outer:
                yield engine.rstrip
            else:
                yield engine.endl
        elif self.strip_outer:
            yield engine.rstrip
    
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
            ', '.join('%s=%r' % (k, getattr(self, k)) for k in (
                'name', 'id', 'class_', 'kwargs_expr',
                'strip_inner', 'strip_outer'
            ) if getattr(self, k))
        )


class Comment(Base):
    
    def __init__(self, inline_content, IE_condition=''):
        super(Comment, self).__init__()
        self.inline_content = inline_content
        self.IE_condition = IE_condition
    
    def render_start(self, engine):
        yield engine.indent()
        yield '<!--'
        if self.IE_condition:
            yield self.IE_condition
            yield '>'
        if self.inline_content:
            yield ' '
            yield self.inline_content
            yield ' '
        if self.children:
            yield engine.inc_depth
            yield engine.endl
    
    def render_end(self, engine):
        if self.children:
            yield engine.dec_depth
            yield engine.indent()
        if self.IE_condition:
            yield '<![endif]'
        yield '-->'
        yield engine.endl
    
    def __repr__(self):
        yield '%s()' % self.__class__.__name__


class Control(Base):
    
    def __init__(self, type, test):
        super(Control, self).__init__()
        self.type = type
        self.test = test
    
    def render_start(self, engine):
        yield engine.assert_newline
        yield engine.indent(-1)
        yield '%% %s %s: ' % (self.type, self.test)
        yield engine.no_strip(engine.endl)
    
    def render_end(self, engine):
        yield engine.assert_newline
        yield engine.indent(-1)
        yield '%% end%s' % self.type
        yield engine.no_strip(engine.endl)
    
    def __repr__(self):
        return '%s(type=%r, test=%r)' % (
            self.__class__.__name__,
            self.type,
            self.test
        )




        
class Source(GreedyBase):
    
    def __init__(self, content, module=False):
        super(Source, self).__init__()
        self.content = content
        self.module = module
    
    def render_start(self, engine):
        if not self.inc_depth(engine):
            if self.module:
                yield '<%! '
            else:
                yield '<% '
        else:
            yield engine.indent()
        yield self.content
        yield engine.endl
        yield engine.inc_depth
    
    def render_end(self, engine):
        if not self.dec_depth(engine):
            yield '%>'
        yield engine.dec_depth
        
        
class Filtered(GreedyBase):

    def __init__(self, content, filter=None):
        super(Filtered, self).__init__()
        self.content = content
        self.filter = filter

    def render_start(self, engine):
        if not self.inc_depth(engine):
            yield '<%% __M_writer(%s(\'\'.join([' % self.filter
            yield engine.endl
        if self.content is not None:
            yield '\'%s%s\',' % (engine.indent(-1), (self.content + engine.endl).encode('unicode-escape').replace("'", "\\'"))
            yield engine.endl
        yield engine.inc_depth

    def render_end(self, engine):
        if not self.dec_depth(engine):
            yield ']))) %>'
        yield engine.dec_depth


class Silent(Base):
    
    def __init__(self, comment):
        super(Silent, self).__init__()
        self.comment = comment
    
    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.comment
        )
    
    def children_to_render(self):
        return []

