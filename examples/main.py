
from mako.template import Template
import haml
import haml.codegen


source = '''

!!! XML
!!!
%head
    %title This should be one line.
%body
    #header
        %img#logo(src='/img/logo.png')
        %ul#top-nav.nav
            - for i in range(2):
                %li= 'Item %02d' % i
    #nav - for i in range(3): %li= i
    #content
        %p
            The content goes in here.
            This is another line of the content.
        %p.warning
            This is a warning.

- content = """
    before
    
    after""".strip()
= content
    		
'''.strip()


print '===== SOURCE ====='
print source.strip()
print

root = haml.parse_string(source)



print '===== NODES ====='
root.print_tree()
print

print '===== MAKO ====='
compiled = haml.generate_mako(root)
print compiled.strip()
print

print '===== COMPILED MAKO ====='
template = Template(compiled)
print template._code.strip()
print

print '===== RENDERED ====='
print template.render_unicode(class_='test', title="MyPage", a='A', b='B', c='C').strip()
print