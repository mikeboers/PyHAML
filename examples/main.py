
from mako.template import Template
import paml
import paml.codegen


source = '''

%head
    %title This should be one line.
%body
    #header
        %img#logo(src='/img/logo.png')
        %ul#top-nav.nav - for i in range(2):
            %li= 'Item %02d' % i
    #content
        %p
            The content goes in here.
            This is another line of the content.
        %p.warning
            This is a warning.
        %<
            This should not have whitespace.
            Can't help it here though.
        %img
        %img>
        %img
    #footer
        &copy; The author, today.

'''.strip()

source = '''

%basic Hello, world!
%outer %inner nested?

%A
    %outer -for i in range(3): %inner complex?!?!

'''


print '===== SOURCE ====='
print source
print

root = paml.parse_string(source)

def print_tree(node, depth=0, inline=False):
    if inline:
        print '-> ' + repr(node),
    else:
        print '|   ' * depth + repr(node),
    depth += int(not inline)
    if node.inline_child:
        print_tree(node.inline_child, depth, True)
    else:
        print
    for child in node.children:
        print_tree(child, depth)

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
print template.render_unicode(class_='test', title="MyPage", a='A', b='B', c='C')
print