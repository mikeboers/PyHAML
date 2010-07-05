
from mako.template import Template
import haml
import haml.codegen


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

%div(class_='content', **{'non-valid':'value'}) content

'''.strip()

print '===== SOURCE ====='
print source
print

root = haml.parse_string(source)



print '===== NODES ====='
root.print_tree()
print

print '===== MAKO ====='
compiled = haml.generate_mako(root)
print compiled
print

print '===== COMPILED MAKO ====='
template = Template(compiled)
print template._code
print

print '===== RENDERED ====='
print template.render_unicode(class_='test', title="MyPage", a='A', b='B', c='C')
print