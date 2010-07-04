
import re
import cgi


class Compiler(object):
    
    def render(self, node):
        return ''.join(self.render_iter(node))
        
    def render_iter(self, node):
        for depth, line in self._visit_node(node):
            if line is not None:
                yield (depth - 1) * ' ' + line + '\n'
    
    def _visit_node(self, node):
        yield 0, node.render_start(self)
        for line in node.render_content(self):
            yield 1, line
        for child in node.children:
            for depth, x in self._visit_node(child):
                yield depth + 1, x
        yield 0, node.render_end(self)
            

class BaseNode(object):
    
    def __init__(self):
        self.children = []
    
    def render_start(self, engine):
        return None
    
    def render_content(self, engine):
        return []
    
    def render_end(self, engine):
        return None
    
    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))


class DocumentNode(BaseNode):
    
    def render_start(self, engine):
        return '<%! from haml.runtime import mako_build_attr_str as __H_attrs %>\\'


class ContentNode(BaseNode):
    
    def __init__(self, content):
        super(ContentNode, self).__init__()
        self.content = content
    
    def render_start(self, engine):
        return self.content
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.content)


class ExpressionNode(ContentNode):
    
    def render_start(self, engine):
        return '${%s}' % self.content.strip()


class TagNode(BaseNode):
    
    self_closing = set('''
        br
        img
        input
    '''.strip().split())
    
    attr_names = 'name id class_ attr_expr is_expr content'.split()
    
    def __init__(self, name, **kwargs):
        super(TagNode, self).__init__()
        for key in self.attr_names:
            setattr(self, key, kwargs.get(key))
        self.name = (name or 'div').lower()
        self.class_ = (self.class_ or '').replace('.', ' ').strip()
    
    def render_start(self, engine):
        
        const_attrs = {}
        if self.id:
            const_attrs['id'] = self.id
        if self.class_:
            const_attrs['class'] = self.class_
        
        if not self.attr_expr:
            attr_str = ''.join(' %s="%s"' % (k, cgi.escape(v)) for k, v in const_attrs.items())
        elif not const_attrs:
            attr_str = '${__H_attrs(%s)}' % self.attr_expr
        else:
            attr_str = '${__H_attrs(%r, %s)}' % (const_attrs, self.attr_expr)
            
        if self.name in self.self_closing:
            return '<%s%s />' % (self.name, attr_str)
        else:
            return '<%s%s>' % (self.name, attr_str)
    
    def render_end(self, engine):
        if self.name not in self.self_closing:
            return '</%s>' % self.name
    
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
            ', '.join('%s=%r' % (k, getattr(self, k)) for k in self.attr_names if getattr(self, k))
        )


class CommentNode(BaseNode):
    
    def render_start(self, engine):
        return '<!--'
    
    def render_end(self, engine):
        return '-->'
    
    def __repr__(self):
        return '%s()' % self.__class__.__name__


class ControlNode(BaseNode):
    
    attr_names = 'name test content'.split()
    
    def __init__(self, **kwargs):
        super(ControlNode, self).__init__()
        for k in self.attr_names:
            setattr(self, k, kwargs.get(k))
    
    def render_start(self, engine):
        return '%% %s %s: ' % (self.name, self.test)
    
    def render_end(self, engine):
        return '%% end %s' % self.name
    
    def __repr__(self):
        return '%s(name=%r, test=%r)' % (
            self.__class__.__name__,
            self.name,
            self.test
        )
    
    
class Parser(object):
    
    def __init__(self):
        self.root = DocumentNode()
        self.stack = [(-1, self.root)]
    
    @property
    def depth(self):
        return self.stack[-1][0]
        
    @property
    def node(self):
        return self.stack[-1][1]
    
    def process_string(self, source):
        for raw_line in source.splitlines():
            if raw_line.startswith('!'):
                self.add_node(ContentNode(raw_line[1:]), depth=self.depth + 1)
                continue
            line = raw_line.lstrip()
            if not line:
                continue
            depth = len(raw_line) - len(line)
            self.process_line(depth, line)
    
    def process_line(self, depth, line):
        
        if not line:
            return
        
        if line.startswith('/'):
            self.add_node(CommentNode(), depth=depth)
            self.process_line(depth + 1, line[1:].lstrip())
            return
        
        m = re.match(r'''
            (?:%(\w+))?       # tag name
            (?:\#([\w-]+))?   # id
            (?:\.([\w\.-]+))? # class
            (?:({.+?}))?      # attribute dict
            (=)?              # expression flag
        ''', line, re.X)
        if m and ''.join(g or '' for g in m.groups()):
            parts = dict(zip(
                TagNode.attr_names,
                m.groups()
            ))
            self.add_node(TagNode(**parts), depth=depth)
            line = line[m.end():].lstrip()
            if parts.get('is_expr'):
                self.add_node(ExpressionNode(line), depth + 1)
                return
            self.process_line(depth + 1, line)
            return
        
        m = re.match(r'''
            -
            \s*
            (for|if|while) # tag name
            \s+
            (.+?):         # control line
        ''', line, re.X)
        if m:
            parts = dict(zip(
                ControlNode.attr_names,
                m.groups()
            ))
            self.add_node(ControlNode(**parts), depth=depth)
            line = line[m.end():].lstrip()
            self.process_line(depth + 1, line)
            return
               
        self.add_node(ContentNode(line), depth=depth)
    
    def add_node(self, node, depth):
        while depth <= self.depth:
            self.stack.pop()
        self.node.children.append(node)
        self.stack.append((depth, node))
        






source = '''

%head
    %title My test document.
    ${next.head()}
%body
    #header
        %img#logo{'src':'/img/logo.png'}
        /
            # Navigation
            Another line of comments goes here.
        %ul#top-nav.nav
            %li Item 1
            %li Item 2
            %li Item 3
    #content
        %p
            The content goes in here.
            This is another line of the content.
        %p.warning.error{'class': class_}
            Paragraph 2.
    #footer
        %ul - for i in range(10):
            %li= 1
<%def name="head()"></%def>
'''

#print source
#print

parser = Parser()
parser.process_string(source)

def print_tree(node, depth=0):
    print '|   ' * depth + repr(node)
    for child in node.children:
        print_tree(child, depth + 1)

print_tree(parser.root)
print
print

print Compiler().render(parser.root)