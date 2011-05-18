

def extract_haml(fileobj, keywords, comment_tags, options):
    """ babel translation token extract function for haml files """

    import haml
    from mako import lexer, parsetree
    from mako.ext.babelplugin import extract_nodes 

    encoding = options.get('input_encoding', options.get('encoding', None))
    template_node = lexer.Lexer(haml.preprocessor(fileobj.read()), input_encoding=encoding).parse()
    for extracted in extract_nodes(template_node.get_children(), keywords, comment_tags, options):
        yield extracted

