
from itertools import chain
import cgi

from . import codegen


class Base(object):

    def __init__(self):
        self.children = []
        self.inline_child = None
        self.inline_parent = None

    def add_child(self, node, inline=False):
        if inline:
            self.inline_child = node
            node.inline_parent = self
        else:
            self.children.append(node)

    def render(self, engine):
        return chain(
            self.render_start(engine),
            self.render_content(engine),
            self.render_end(engine),
        )

    def render_start(self, engine):
        return []

    def children_to_render(self):
        return self.children

    def render_content(self, engine):
        to_chain = []
        if self.inline_child:
            to_chain = [
                self.inline_child.render_start(engine),
                self.inline_child.render_content(engine),
                self.inline_child.render_end(engine),
            ]
        for child in self.children_to_render():
            to_chain.append(child.render(engine))
        return chain(*to_chain)

    def render_end(self, engine):
        return []

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def print_tree(self, _depth=0, _inline=False):
        if _inline:
            print '-> ' + repr(self),
        else:
            print '|   ' * _depth + repr(self),
        _depth += int(not _inline)
        if self.inline_child:
            self.inline_child.print_tree(_depth, True)
        else:
            print
        for child in self.children:
            child.print_tree(_depth)


class GreedyBase(Base):
    
    def __init__(self, *args, **kwargs):
        super(GreedyBase, self).__init__(*args, **kwargs)
        self._greedy_parent = None

    @classmethod
    def with_parent(cls, parent, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj._greedy_parent = parent
        return obj

    @property
    def outermost_node(self):
        x = self
        while x._greedy_parent is not None:
            x = x._greedy_parent
        return x

    @property
    def _depth_name(self):
        return '%s.depth' % self.__class__.__name__

    def inc_depth(self, engine):
        depth = engine.node_data.get(self._depth_name, 0)
        engine.node_data[self._depth_name] = depth + 1
        return depth

    def dec_depth(self, engine):
        depth = engine.node_data[self._depth_name] - 1
        engine.node_data[self._depth_name] = depth
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



class GreedyContent(Content, GreedyBase):
    pass

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

    def __init__(self, name, id, class_,
            kwargs_expr=None,
            object_reference=None,
            object_reference_prefix=None,
            self_closing=False,
            strip_inner=False,
            strip_outer=False,
        ):

        super(Tag, self).__init__()

        self.name = (name or 'div').lower()
        self.id = id
        self.class_ = (class_ or '').replace('.', ' ').strip()
        self.kwargs_expr = kwargs_expr
        self.object_reference = object_reference
        self.object_reference_prefix = object_reference_prefix
        self.self_closing = self_closing
        self.strip_inner = strip_inner
        self.strip_outer = strip_outer

    def render_start(self, engine):

        const_attrs = {}
        if self.id:
            const_attrs['id'] = self.id
        if self.class_:
            const_attrs['class'] = self.class_

        kwargs_expr = self.kwargs_expr or ''

        # Object references are actually handled by the attribute formatting
        # function.
        if self.object_reference:
            kwargs_expr += (', ' if kwargs_expr else '') + '__obj_ref=' + self.object_reference
            if self.object_reference_prefix:
                kwargs_expr += ', __obj_ref_pre=' + self.object_reference_prefix

        if kwargs_expr:
            try:
                # HACK: This is really freaking dangerous...
                # If we can evaluate the expression with no content then we
                # can go ahead and use
                const_attrs.update(eval('dict(%s)' % kwargs_expr, {}))
            except (NameError, ValueError, KeyError):
                pass
            else:
                kwargs_expr = None

        if not kwargs_expr:
            attr_str = codegen.mako_build_attr_str(const_attrs)
        elif not const_attrs:
            attr_str = '<%% __M_writer(__P_attrs(%s)) %%>' % kwargs_expr
        else:
            attr_str = '<%% __M_writer(__P_attrs(%r, %s)) %%>' % (const_attrs, kwargs_expr)

        if self.strip_outer:
            yield engine.lstrip
        elif not self.inline_parent:
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
                if self.strip_inner or self.inline_child:
                    yield engine.rstrip
                else:
                    yield engine.endl
                    yield engine.inc_depth

    def render_content(self, engine):
        if self.inline_child:
            return chain(
                [engine.lstrip, engine.rstrip],
                super(Tag, self).render_content(engine),
                [engine.lstrip, engine.rstrip],
            )
        else:
            return super(Tag, self).render_content(engine)

    def render_end(self, engine):
        if self.strip_inner or self.inline_child:
            yield engine.lstrip
        if not (self.self_closing or self.name in self.self_closing_names):
            if self.children:
                yield engine.dec_depth
                yield engine.indent()
            yield '</%s>' % self.name
            if self.strip_outer:
                yield engine.rstrip
            elif not self.inline_parent:
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
        yield engine.line_continuation
        yield engine.indent(-1)
        yield '%% %s %s: ' % (self.type, self.test)
        yield engine.no_strip(engine.endl)

    def render_end(self, engine):
        yield engine.line_continuation
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
    
    def __repr__(self):
        return '%s(%r%s)' % (
            self.__class__.__name__,
            self.content,
            ', module=True' if self.module else ''
        )


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



class Doctype(Base):
    doctypes = {
        'xml': {
            None: """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">""",
            "strict": """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">""",
            "frameset": """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">""",
            "5": """<!DOCTYPE html>""",
            "1.1": """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">""",
            "basic": """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML Basic 1.1//EN" "http://www.w3.org/TR/xhtml-basic/xhtml-basic11.dtd">""",
            "mobile": """<!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.2//EN" "http://www.openmobilealliance.org/tech/DTD/xhtml-mobile12.dtd">""",
            "rdfa": """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML+RDFa 1.0//EN" "http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd">""",
        }, 'html': {
            None: """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">""",
            "strict": """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">""",
            "frameset": """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN" "http://www.w3.org/TR/html4/frameset.dtd">"""
    }}

    def __init__(self, name=None, charset=None):
        super(Doctype, self).__init__()
        self.name = name.lower() if name else None
        self.charset = charset

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.name,
            self.charset
        )

    def render_start(self, engine):
        if self.name in ('xml', 'html'):
            mode = self.name
            engine.node_data['Doctype.mode'] = mode
        else:
            mode = engine.node_data.get('Doctype.mode', 'html')
        if self.name == 'xml':
            charset = self.charset or 'utf-8'
            yield "<?xml version='1.0' encoding='%s' ?>" % charset
            yield engine.no_strip('\n')
            return
        yield self.doctypes[mode][self.name]
        yield engine.no_strip('\n')
