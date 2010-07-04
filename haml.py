
import re
import cgi


class Compiler(object):
    
    def render(self, node):
        return ''.join(self.render_iter(node))
        
    def render_iter(self, node):
        for indent, line in self._visit_node(node):
            if line is not None:
                yield (indent - 1) * ' ' + line + '\n'
    
    def _visit_node(self, node):
        yield 0, node.render_start(self)
        for line in node.render_content(self):
            yield 1, line
        for child in node.children:
            for indent, x in self._visit_node(child):
                yield indent + 1, x
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


class DocumentNode(BaseNode):
    
    def render_start(self, engine):
        return '<%! from haml.runtime import mako_build_attr_str as __H_attrs %>\\'


class ContentNode(BaseNode):
    
    def __init__(self, content):
        super(ContentNode, self).__init__()
        self.content = content
    
    def render_start(self, engine):
        return self.content
        

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


class CommentNode(BaseNode):
    
    def render_start(self, engine):
        return '<!--'
    
    def render_end(self, engine):
        return '-->'


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
    
    
class Parser(object):
    
    def __init__(self):
        self.root = DocumentNode()
        self.stack = [(-1, self.root)]
    
    @property
    def indent(self):
        return self.stack[-1][0]
        
    @property
    def node(self):
        return self.stack[-1][1]
    
    def process_string(self, source):
        for raw_line in source.splitlines():
            if raw_line.startswith('!'):
                self.add_node(ContentNode(raw_line[1:]), indent=self.indent + 1)
                continue
            line = raw_line.lstrip()
            if not line:
                continue
            indent = len(raw_line) - len(line)
            self.process_line(indent, line)
    
    def process_line(self, indent, line):
        if line.startswith('/'):
            self.add_node(CommentNode(), indent=indent)
            indent += 1
            line = line[1:].strip()
            if not line:
                return
        m = re.match(r'''
            (?:%(\w+))?       # tag name
            (?:\#([\w-]+))?   # id
            (?:\.([\w\.-]+))? # class
            (?:({.+?}))?      # attribute dict
            (=)?              # expression flag
            (?:
                \s+
                (.+)          # content
            )?
            $
        ''', line, re.X)
        if m:
            parts = dict(zip(
                TagNode.attr_names,
                m.groups()
            ))
            self.add_node(TagNode(**parts), indent=indent)
            content = parts.get('content')
            if content:
                indent += 1
                if parts.get('is_expr'):
                    self.add_node(ContentNode('${%s}' % content.strip()), indent=indent)
                    line = ''
                else:
                    line = content.strip()
            else:
                line = ''
        m = re.match(r'''
            -
            \s*
            (for|if|while) # tag name
            \s+
            (.+?):         # control line
            (.*)           # content
        ''', line, re.X)
        if m:
            parts = dict(zip(
                ControlNode.attr_names,
                m.groups()
            ))
            self.add_node(ControlNode(**parts), indent=indent)
            content = parts.get('content')
            if content:
                line = content
                indent += 1
            else:
                line = ''            
        if line:     
            self.add_node(ContentNode(line), indent=indent)
    
    def add_node(self, node, indent):
        while indent <= self.indent:
            self.stack.pop()
        self.node.children.append(node)
        self.stack.append((indent, node))
        






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

print source
print

parser = Parser()
parser.process_string(source)

print Compiler().render(parser.root)