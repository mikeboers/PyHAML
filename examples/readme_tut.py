import haml
import mako.template

# 1. Write your HAML.
haml_source = '.content Hello, World!'

# 2. Parse your HAML source into a node tree.
haml_nodes = haml.parse_string(haml_source)

# 3. Generate Mako template source from the node tree.
mako_source = haml.generate_mako(haml_nodes)

# 4. Render the template.
print mako.template.Template(mako_source).render_unicode()