import re
import ast
import operator

def parse_args(input, end=')'):
    chunks = re.split(r'(,|%s)' % re.escape(end), input)
    output = []
    
    # Continue processing chunks as long as we keep getting something.
    last_output = -1
    while len(output) != last_output:
        last_output = len(output)
        
        # Extract kwarg name.
        m = re.match(r'\s*(?::?([\w-]+)\s*=>?|(\*{1,2}))', chunks[0])
        if m:
            name = m.group(1) or m.group(2)
            chunks[0] = chunks[0][m.end():]
        else:
            name = None
    
        # Keep finding chunks until it compiles:
        for i in xrange(1, len(chunks), 2):
            source = ''.join(chunks[:i]).lstrip()
            try:
                parsed = ast.parse(source, mode='eval')
            except SyntaxError as e:
                continue
            
            output.append((name, source, parsed))
            next_delim = chunks[i]                
            chunks = chunks[i + 1:]
            break
        
        else:
            break
        
        if next_delim == end:
            break
        
    return output, ''.join(chunks)




def literal_eval(node_or_string):
    """
    Safely evaluate an expression node or a string containing a Python
    expression.  The string or node provided may only consist of the following
    Python literal structures: strings, numbers, tuples, lists, dicts, booleans,
    and None.
    """
    _safe_names = {
        'None': None,
        'True': True,
        'False': False,
        'dict': dict,
        'list': list,
        'sorted': sorted
    }
    
    if isinstance(node_or_string, basestring):
        node_or_string = parse(node_or_string, mode='eval')
        
    if isinstance(node_or_string, ast.Expression):
        node_or_string = node_or_string.body
        
    def _convert(node):
        
        if isinstance(node, ast.Str):
            return node.s
        
        elif isinstance(node, ast.Num):
            return node.n
        
        elif isinstance(node, ast.Tuple):
            return tuple(map(_convert, node.elts))
        
        elif isinstance(node, ast.List):
            return list(map(_convert, node.elts))
        
        elif isinstance(node, ast.Dict):
            return dict((_convert(k), _convert(v)) for k, v
                        in zip(node.keys, node.values))
        
        elif isinstance(node, ast.Name):
            if node.id in _safe_names:
                return _safe_names[node.id]
        
        elif isinstance(node, ast.BinOp):
            left = _convert(node.left)
            right = _convert(node.right)
            op = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.div,
                ast.Mod: operator.mod
            }.get(type(node.op), None)
            if op:
                return op(left, right)
        
        elif isinstance(node, ast.Call):
            func = _convert(node.func)
            args = map(_convert, node.args)
            kwargs = dict((kw.arg, _convert(kw.value)) for kw in node.keywords)
            if node.starargs:
                args.extend(_convert(node.starargs))
            if node.kwargs:
                kwargs.update(_convert(node.kwargs))
            return func(*args, **kwargs)
        
        elif isinstance(node, ast.Attribute):
            if not node.attr.startswith('_'):
                return getattr(_convert(node.value), node.attr)
        
        raise ValueError('malformed string: %r' % node)
    return _convert(node_or_string)


if __name__ == '__main__':
    
    signatures = '''

(1, 2, 3) more
(key='value') more
(**dict(key='value')) more
(*[1, 2, 3]) more
{:class => "code", :id => "message"} Hello
(class_='before %s after' % 'middle') hello
(data-crud=dict(id=34, url='/api')) crud goes here
(u'unicode!', b'bytes!')
(' '.join(['hello', 'there'])) after
([i for i in 'hello'])

'''.strip().splitlines()
    for sig in signatures:
        print sig
        args, remaining = parse_args(sig[1:], {'(':')', '{':'}'}[sig[0]])
        
    
        for key, source, root in args:
            try:
                value = literal_eval(root)
                print '%s: %r' % (key, value)
            except ValueError as e:
                print '%s -> %s' % (key, e)
        
        print repr(remaining), 'remains'
        print
        
