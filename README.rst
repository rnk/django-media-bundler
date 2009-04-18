Django Media Bundler
====================

Django Media Bundler is a Django plugin bundles up your Javascript, CSS, and
icons for production, while still being easy to debug during development.  To
use the media bundler, you just have to describe the media you would like to be
bundled together in your ``settings.py`` file, and run ``python manage.py
bundle_media``.  The Media Bundler is inspired by the Rails' `Asset Packager`_
plugin, which helps do roughly the same things for Rails.  This is not the first
Django application for this task, and it is probably not the last.  You can find
a good comparison of other media bundling tools here_.

.. _Asset Packager: http://synthesis.sbecker.net/pages/asset_packager
.. _here: http://qinsb.blogspot.com/2009/02/alternatives-to-django-media-bundler.html

Supported Bundle Types
----------------------

- **Javascript**: The media bundler will concatenate and optionally minify your
  Javascript.  It also lets you to defer loading Javascript until the end of the
  document, as described in here_.  We do not support packing, because that has
  been shown to slow down Javascript execution.

- **CSS**: The media bundler will concatenate and optionally minify CSS.  It
  does not defer CSS, because that makes the page appear to load more slowly.

- **Image Sprites**: The media bundler will take a list of your icons and
  arrange them into a new and compact PNG image sprite.  It will then run
  pngcrush_ on the resulting image, and generate CSS class names and rules to
  display your icons.

.. _here: http://developer.yahoo.net/blog/archives/2007/07/high_performanc_5.html
.. _pngcrush: http://pmt.sourceforge.net/pngcrush/

Dependencies
------------

- Python 2.5+

For image sprites:

- `Python Imaging Library`_ (spelled python-imaging under Ubuntu)
- pngcrush_

.. _Python Imaging Library: http://www.pythonware.com/products/pil/

Installation
------------

The media-bundler is a reusable app, so to install it all you have to do is
clone the source tree, put it somewhere in Django's ``PYTHONPATH``, and add it
to ``INSTALLED_APPS`` in ``settings.py``.

Usage
-----

Describe the Javascript and CSS bundles you would like to create in
``settings.py`` roughly like so::

  MEDIA_BUNDLES = (
      {"type": "javascript",
       "name": "myapp_scripts",
       "path": MEDIA_ROOT + "/scripts/",
       "url": MEDIA_URL + "/scripts/",
       "minify": True,  # If you want to minify your source.
       "files": (
           "foo.js",
           "bar.js",
           "baz.js",
       )},
      {"type": "css",
       "name": "myapp_styles",
       "path": MEDIA_ROOT + "/styles/",
       "url": MEDIA_URL + "/styles/",
       "minify": True,  # If you want to minify your source.
       "files": (
           "foo.css",
           "bar.css",
           "baz.css",
           "myapp-sprites.css"  # Include this generated CSS file.
       )},
      {"type": "png-sprite",
       "name": "myapp_sprites",
       "path": MEDIA_ROOT + "/images/",
       "url": MEDIA_URL + "/images/",
       # Where the generated CSS rules go.
       "css_file": MEDIA_ROOT + "/styles/myapp-sprites.css",
       "files": (
           "foo.png",
           "bar.png",
           "baz.png",
       )},
  )

By default, deferring is enabled, and bundling is disabled when
``settings.DEBUG`` is ``True``.  You can override those values in your settings
module.  See the ``media_bundle.default_settings`` module for more info.  

To source your Javascript and CSS, put ``{% load bundler_tags %}`` at the top of
your template, and wherever you used to write this::

  <script type="text/javascript" src="/url/myscript.js"></script>
  <link rel="stylesheet" type="text/css" href="/url/mystyle.css"/>

you should write this::

  {% javascript "js_bundle_name" "myscript.js" %}
  {% css "css_bundle_name" "mystyle.css" %}

If you want, you can load all the files in a bundle at once with the
``load_bundle`` tag::

  {% load_bundle "js_bundle_name" %}
  {% load_bundle "css_bundle_name" %}

``load_bundle`` will add ``{% css %}`` and ``{% javascript %}`` tags for all
the files in the bundle.

If you are deferring your Javascript, then at the bottom of your base template
you should insert the tag ``{% deferred_content %}``.  We recommend opening a
second head tag after your body and putting it there.
