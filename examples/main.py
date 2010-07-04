
from mako.template import Template
import paml
import paml.codegen


source = '''

%head
    %title My test document.
%body
    #header
        %img#logo(src='/img/logo.png')
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
        %p.warning.error(class_=class_)
            Paragraph 2.
    #footer %ul - for i in range(3): %li= i
    #id.class first
    .class#id second
    #test-id(key={}.get('value', 'default')) test
<%def name="head()"></%def>

'''.strip()

print '===== SOURCE ====='
print source
print

root = paml.parse_string(source)

def print_tree(node, depth=0):
    print '|   ' * depth + repr(node)
    for child in node.children:
        print_tree(child, depth + 1)

print '===== NODES ====='
print_tree(root)
print

print '===== MAKO ====='
compiled = paml.generate_mako(root)
print compiled
print

print '===== COMPILED MAKO ====='
template = Template(compiled)
print template._code
print

print '===== RENDERED ====='
print template.render_unicode(class_='test')
print