"""
Download a list of existing languages.
Example::
    isocode,base_isocode,changetime
    ja_JP,en_GB,2015-06-07T12:36:47.1Z
    en_GB,,2015-06-07T12:33:35Z

"""
from webtranslate.bottle import route, abort, response
from webtranslate.protect import protected
from webtranslate import config, data

def get_newest_change(lang):
    """
    Decide when the provided language was last changed.

    @param lang: Language to inspect.
    @type  lang: L{Language}

    @return: Time stamp of the last change, if it exists.
    @rtype:  C{None} or L{Stamp}
    """
    newest = None

    for chgs in lang.changes.values():
        for chg in chgs:
            if newest is None or newest < chg.stamp:
                newest = chg.stamp
    return newest

@route('/download-list/<prjname>', method = 'GET')
@protected(['download-list', 'prjname', '-'])
def download_list(userauth, prjname):
    pmd = config.cache.get_pmd(prjname)
    if pmd is None:
        abort(404, "Project does not exist")
        return

    pdata = pmd.pdata
    response.content_type = 'text/plain; charset=UTF-8'
    lines = ['isocode,name,base_isocode,changetime']
    for lng, ldata in pdata.languages.items():
        tstamp = get_newest_change(ldata)
        if tstamp is None:
            text = "--no-time-available--"
        else:
            text = data.encode_stamp(tstamp)

        if pdata.base_language == lng:
            parent_lng = ''
        else:
            parent_lng = pdata.base_language

        line = "{},{},{},{}".format(ldata.name, ldata.info.name, parent_lng, text)
        lines.append(line)

    return '\n'.join(lines) + '\n'

