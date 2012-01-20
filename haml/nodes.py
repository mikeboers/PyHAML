
from itertools import chain
import cgi
import re

from . import codegen
from . import runtime


class Base(object):

    def __init__(self):
        self.inline_child = None
        self.children = []

    def add_child(self, node, inline=False):
        if inline:
            self.inline_child = node
        else:
            self.children.append(node)
    
    def consume_sibling(self, node):
        return False

    def render(self, engine):
        return chain(
            self.render_start(engine),
            self.render_content(engine),
            self.render_end(engine),
        )

    def render_start(self, engine):
        return []

    def render_content(self, engine):
        to_chain = []
        if self.inline_child:
            to_chain.append(self.inline_child.render(engine))
        for child in self.children:
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


class FilterBase(Base):

    def __init__(self, *args, **kwargs):
        super(FilterBase, self).__init__(*args, **kwargs)
        self._content = []

    def add_line(self, indent, content):
        self._content.append((indent, content))

    def iter_dedented(self):
        indent_to_remove = None
        for indent, content in self._content:
            if indent_to_remove is None:
                yield content
                if content:
                    indent_to_remove = len(indent)
            else:
                yield (indent + content)[indent_to_remove:]


class GreedyBase(Base):
    
    def __init__(self, *args, **kwargs):
        super(GreedyBase, self).__init__(*args, **kwargs)
        self._greedy_root = self

    def add_child(self, child, *args):
        super(GreedyBase, self).add_child(child, *args)
        child._greedy_root = self._greedy_root


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
            filters = self._greedy_root.filters
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
                # HACK: If we can evaluate the expression without error then
                # we don't need to do it at runtime. This is possibly quite
                # dangerous. We are trying to protect ourselves but I can't
                # guarantee it.
                kwargs_code = compile('__update__(%s)' % kwargs_expr, '<kwargs_expr>', 'eval')
                sandbox = __builtins__.copy()
                del sandbox['__import__']
                del sandbox['eval']
                del sandbox['execfile']
                def const_attrs_update(*args, **kwargs):
                    map(const_attrs.update, args)
                    const_attrs.update(kwargs)
                sandbox['__update__'] = const_attrs_update
                eval(kwargs_code, sandbox)
            except (NameError, ValueError, KeyError):
                pass
            else:
                kwargs_expr = None

        if not kwargs_expr:
            attr_str = runtime.attribute_str(const_attrs)
        elif not const_attrs:
            attr_str = '<%% __M_writer(__HAML.attribute_str(%s)) %%>' % kwargs_expr
        else:
            attr_str = '<%% __M_writer(__HAML.attribute_str(%r, %s)) %%>' % (const_attrs, kwargs_expr)

        if self.strip_outer:
            yield engine.lstrip
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

class MixinDef(Tag):

    def __init__(self, name, argspec):
        super(MixinDef, self).__init__(
            '%def', # tag name
            None, # ID
            None, # class
            'name=%r' % ('%s(%s)' % (name, argspec or '')), # kwargs expr
            strip_inner=True,
        )


class MixinCall(Tag):

    def __init__(self, name, argspec):
        super(MixinCall, self).__init__(
            '%call', # tag name
            None, # ID
            None, # class
            'expr=%r' % ('%s(%s)' % (name, argspec or '')), # kwargs expr
        )


class HTMLComment(Base):

    def __init__(self, inline_content, IE_condition=''):
        super(HTMLComment, self).__init__()
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
        self.elifs = []
        self.else_ = None

    def consume_sibling(self, node):
        if not isinstance(node, Control):
            return False
        if node.type == 'elif':
            self.elifs.append(node)
            return True
        if node.type == 'else' and self.else_ is None:
            self.else_ = node
            return True
    
    def print_tree(self, depth, inline=False):
        super(Control, self).print_tree(depth)
        for node in self.elifs:
            node.print_tree(depth)
        if self.else_ is not None:
            self.else_.print_tree(depth)
            
    def render(self, engine):
        to_chain = [self.render_start(engine), self.render_content(engine)]
        for node in self.elifs:
            to_chain.append(node.render(engine))
        if self.else_:
            to_chain.append(self.else_.render(engine))
        to_chain.append(self.render_end(engine))
        return chain(*to_chain)
        
    def render_start(self, engine):
        yield engine.line_continuation
        yield engine.indent(-1)
        if self.test is not None:
            yield '%% %s %s: ' % (self.type, self.test)
        else:
            yield '%% %s: ' % (self.type)
        yield engine.no_strip(engine.endl)

    def render_end(self, engine):
        if self.type in ('else', 'elif'):
            return
        yield engine.line_continuation
        yield engine.indent(-1)
        yield '%% end%s' % self.type
        yield engine.no_strip(engine.endl)

    def __repr__(self):
        if self.test is not None:
            return '%s(type=%r, test=%r)' % (
                self.__class__.__name__,
                self.type,
                self.test
            )
        else:
            return '%s(type=%r)' % (self.__class__.__name__, self.type)


class Python(FilterBase):

    def __init__(self, content, module=False):
        super(Python, self).__init__()
        if content.strip():
            self.add_line('', content)
        self.module = module

    def render(self, engine):
        if self.module:
            yield '<%! '
        else:
            yield '<% '
        yield engine.endl
        for line in self.iter_dedented():
            yield line
            yield engine.endl
        yield '%>'
        yield engine.endl_no_break
    
    def __repr__(self):
        return '%s(%r%s)' % (
            self.__class__.__name__,
            self._content,
            ', module=True' if self.module else ''
        )


class Filter(FilterBase):

    def __init__(self, content, filter):
        super(Filter, self).__init__()
        if content and content.strip():
            self.add_line('', content)
        self.filter = filter

    def _escape_expressions(self, source):
        parts = re.split(r'(\${.*?})', source)
        for i in range(0, len(parts), 2):
            parts[i] = parts[i] and ('<%%text>%s</%%text>' % parts[i])
        return ''.join(parts)

    def render(self, engine):
        # Hopefully this chain respects proper scope resolution.
        yield '<%%block filter="locals().get(%r) or globals().get(%r) or getattr(__HAML.filters, %r, UNDEFINED)">' % (self.filter, self.filter, self.filter)
        yield engine.endl_no_break
        yield self._escape_expressions(engine.endl.join(self.iter_dedented()).strip())
        yield '</%block>'
        yield engine.endl

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self._content,
                self.filter)


class HAMLComment(Base):

    def __init__(self, comment):
        super(HAMLComment, self).__init__()
        self.comment = comment

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.comment
        )

    def render(self, engine):
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
