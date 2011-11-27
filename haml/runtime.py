import re
import cgi

from . import filters

_attr_sort_order = {
    'id': -3,
    'class': -2,
    'http-equiv': -1, # for meta
    'checked': 1,
    'selected': 1,
}


_camelcase_re = re.compile(r'(?<!^)([A-Z])([A-Z]*)')
def adapt_camelcase(name, seperator):
    return _camelcase_re.sub(lambda m: seperator + m.group(0), name).lower()


def _format_mako_attr_pair(k, v):
    if v is True:
        v = k
    return ' %s="%s"' % (k, cgi.escape("%s" % v))


def flatten_attr_list(input):
    if not input:
        return
    if isinstance(input, basestring):
        yield input
        return
    try:
        input = iter(input)
    except TypeError:
        yield input
        return
    for element in input:
        if element:
            for sub_element in flatten_attr_list(element):
                yield sub_element


def flatten_attr_dict(prefix_key, input):
    if not isinstance(input, dict):
        yield prefix_key, input
        return
    for key, value in input.iteritems():
        yield prefix_key + '-' + key, value


def attribute_str(*args, **kwargs):
    x = {}
    for arg in args:
        x.update(arg)
    x.update(kwargs)
    obj_ref = x.pop('__obj_ref', None)
    obj_ref_prefix = x.pop('__obj_ref_pre', None)
    if x.pop('__adapt_camelcase', True):
        x = dict((adapt_camelcase(k, '-'), v) for k, v in x.iteritems())
    x['id'] = flatten_attr_list(
        x.pop('id', [])
    )
    x['class'] = list(flatten_attr_list(
        [x.pop('class', []), x.pop('class_', [])]
    ))
    if obj_ref:
        class_name = adapt_camelcase(obj_ref.__class__.__name__, '_')
        x['id'] = filter(None, [obj_ref_prefix, class_name, getattr(obj_ref, 'id', None)])
        x['class'].append((obj_ref_prefix + '_' if obj_ref_prefix else '') + class_name)
    x['id'] = '_'.join(map(str, x['id']))
    x['class'] = ' '.join(map(str, x['class']))
    pairs = []
    for k, v in x.iteritems():
        pairs.extend(flatten_attr_dict(k, v))
    pairs.sort(key=lambda pair: (_attr_sort_order.get(pair[0], 0), pair[0]))
    return ''.join(_format_mako_attr_pair(k, v) for k, v in pairs if v)


