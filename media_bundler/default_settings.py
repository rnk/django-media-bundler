# media_bundler/default_settings.py

"""
These are the default settings for media_bunder.

You can copy, paste, and modify these values into your own settings.py file.
"""

from django.conf import settings

# This flag determines whether to enable bundling or not.  To assist in
# debugging, we recommend keeping files separate during development and bundle
# them during production, so by default we just use settings.DEBUG, but you can
# override that value if you wish.
USE_BUNDLES = settings.DEBUG

# This puts your JavaScript at the bottom of your templates instead of the top
# in order to allow the page to load before script execution, as described in
# YUI rule #5:
# http://developer.yahoo.net/blog/archives/2007/07/high_performanc_5.html
DEFER_JAVASCRIPT = True

MEDIA_BUNDLES = (
    # This should contain something like:

    #{"type": "javascript",
    # "name": "myapp_scripts",
    # "path": MEDIA_ROOT + "/scripts/",
    # "url": MEDIA_URL + "/scripts/",
    # "compression": None,  # other values are "minify" and "pack".
    # "files": ("foo.js", "bar.js", "baz.js")},

    #{"type": "css",
    # "name": "myapp_styles",
    # "path": MEDIA_ROOT + "/styles/",
    # "url": MEDIA_URL + "/styles/",
    # "compression": None,  # other values are "minify".
    # "files": ("foo.css", "bar.css", "baz.css")},

    ## Image bundling is not implemented yet, but this is how it might look.
    #{"type": "sprite",
    # "name": "myapp_sprites",
    # "path": MEDIA_ROOT + "/images/",
    # "url": MEDIA_URL + "/images/",
    # "files": ("foo.png", "bar.png", "baz.png")},
)
