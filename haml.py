
import re
import cgi

class Engine(object):
    pass

class BaseNode(object):
    
    def __init__(self):
        self.children = []
        self.indent = -1
    
    def render(self):
        return self.render_children()
    
    def render_children(self):
        return ''.join(x.render() for x in self.children)
    
    @property
    def indent_str(self):
        return '  ' * self.indent
    
    def normalize_indent(self, indent=-1):
        self.indent = indent
        for child in self.children:
            child.normalize_indent(indent + 1)

class ContentNode(BaseNode):
    
    def __init__(self, content):
        super(ContentNode, self).__init__()
        self.content = content
    
    def render(self):
        return (
            self.indent_str + self.content + '\n' +
            self.render_children()
        )

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
    
    def render(self):
        
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
            return (
                self.indent_str + ('<%s%s />' % (self.name, attr_str)) + '\n'
            )
        
        return (
            self.indent_str + ('<%s%s>' % (self.name, attr_str)) + '\n' +
            self.render_children() +
            self.indent_str + ('</%s>' % self.name) + '\n'
        )


class ControlNode(BaseNode):
    
    attr_names = 'name test content'.split()
    
    def __init__(self, **kwargs):
        super(ControlNode, self).__init__()
        for k in self.attr_names:
            setattr(self, k, kwargs.get(k))
    
    def render(self):
        return (
            self.indent_str + ('%% %s %s: ' % (self.name, self.test)) + '\n' + 
            self.render_children() +
            self.indent_str + ('%% end %s' % self.name) + '\n'
        )
    
    
class Compiler(object):
    
    def __init__(self, engine):
        self.engine = engine
        self.root = BaseNode()
        self.stack = [self.root]
    
    @property
    def tip(self):
        return self.stack[-1]
    
    def process_string(self, source):
        for raw_line in source.splitlines():
            if raw_line.startswith('!'):
                self.add_node(ContentNode(raw_line[1:]), indent=self.tip.indent + 1)
                continue
            line = raw_line.strip()
            if not line:
                continue
            indent = len(raw_line) - len(line)
            self.process_line(indent, line)
    
    def process_line(self, indent, line):
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
        ''', line, re.X)
        if m and ''.join(x or '' for x in m.groups()):
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
    
    def add_node(self, node, indent=None):
        if indent is not None:
            node.indent = indent
        while node.indent <= self.tip.indent:
            self.stack.pop()
        self.tip.children.append(node)
        self.stack.append(node)
        






source = '''

%head
    %title My test document.
    ${next.head()}
%body
    #header
        %img#logo{'src':'/img/logo.png'}
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
!       %p
!           This should not be touched.
    #footer
        %ul - for i in range(10):
            %li= 1
<%def name="head()"></%def>
'''


c = Compiler(Engine())
c.process_string(source)
c.root.normalize_indent()

print '<%! from haml.runtime import mako_build_attr_str as __H_attrs %>\\'
print c.root.render()