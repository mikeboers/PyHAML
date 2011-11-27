import subprocess
import cgi


def plain(src):
    return src


def escaped(src):
    return cgi.escape(src)


def cdata(src):
    # This should only apply if the runtime is in XML mode.
    return '<![CDATA[%s]]>' % (src.replace(']]>', ']]]]><![CDATA[>'))


def javascript(src):
    return '<script>%s</script>' % cdata(src)


def css(src):
    return '<style>%s</style>' % cdata(src)


def sass(src, scss=False):
    args = ['sass', '--style', 'compressed']
    if scss:
        args.append('--scss')
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    out, err = proc.communicate(src)
    if out:
        out = css(out.rstrip())
    if err:
        out += '<div class="sass-error">%s</div>' % cgi.escape(err)
    return out

def scss(src):
    return sass(src, scss=True)

