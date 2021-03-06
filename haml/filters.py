import subprocess
import cgi

from six import StringIO

def plain(src):
    return src


def escaped(src):
    return cgi.escape(src)


def cdata(src, comment=False):
    # This should only apply if the runtime is in XML mode.
    block_open  = ('/*' if comment else '') + '<![CDATA[' + ('*/' if comment else '')
    block_close = ('/*' if comment else '') + ']]>'       + ('*/' if comment else '')
    # This close/reopen is only going to work with xhtml.
    return block_open + (src.replace(']]>', ']]]]><![CDATA[>')) + block_close


def javascript(src):
    return '<script>%s</script>' % cdata(src, True)


def css(src):
    return '<style>%s</style>' % cdata(src, True)


def sass(src, scss=False):
    args = ['sass', '--style', 'compressed']
    if scss:
        args.append('--scss')
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    out, err = proc.communicate(src.encode('utf-8'))
    if out:
        out = css(out.rstrip().decode('utf-8'))
    if err:
        out += '<div class="sass-error">%s</div>' % cgi.escape(err.decode('utf-8'))
    return out


def scss(src):
    return sass(src, scss=True)

def less(src):
    import lesscpy
    return css(lesscpy.compile(StringIO(src), minify=True))

def coffeescript(src):
    args = ['coffee', '--compile', '--stdio']
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    out, err = proc.communicate(src.encode('utf-8'))
    if out:
        out = javascript(out)
    if err:
        out += '<div class="coffeescript-error">%s</div>' % cgi.escape(err)
    return out.decode('utf-8')


