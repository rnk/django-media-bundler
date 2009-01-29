# media_bundler/cssmin.py

# Original source code:
# http://stackoverflow.com/questions/222581/python-script-for-minifying-css

# This is obviously a hacky script, and it probably has bugs.

import re

def minify_css(css):
    # remove comments - this will break a lot of hacks :-P
    css = re.sub(r'\s*/\*\s*\*/', "$$HACK1$$", css)
    css = re.sub(r'/\*[\s\S]*?\*/', "", css)
    css = css.replace("$$HACK1$$", '/**/') # preserve IE<6 comment hack
    # url() don't need quotes
    css = re.sub(r'url\((["\'])([^)]*)\1\)', "url(\\2)", css)
    # spaces may be safely collapsed as generated content will collapse them anyway
    css = re.sub(r'\s+', " ", css)
    return "".join(generate_rules(css))

def generate_rules(css):
    for rule in re.findall(r'([^{]+){([^}]*)}', css):
        selectors = []
        for selector in rule[0].split(','):
            selectors.append(selector.strip())
        # order is important, but we still want to discard repetitions
        properties = {}
        porder  = []
        for prop in re.findall('(.*?):(.*?)(;|$)', rule[1]):
            key = prop[0].strip().lower()
            if key not in porder:
                porder.insert(0, key)
            properties[ key ] = prop[1].strip()
        porder.reverse()
        # output rule if it contains any declarations
        if len(properties) > 0:
            s = ";".join(key + ":" + properties[key] for key in porder)
            yield ",".join(selectors) + "{" + s + "}"
