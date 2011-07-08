
from mako.template import Template
import haml
import haml.codegen


source = '''

- if False:
    AAA
- else:
    BBB

'''


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

# print '===== COMPILED MAKO ====='
template = Template(compiled)
# print template._code.strip()
# print

print '===== RENDERED ====='
print template.render_unicode(class_='test', title="MyPage", a='A', b='B', c='C').strip()
print