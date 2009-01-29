# media_bundler/management/commands/bundle_media.py

from __future__ import with_statement

"""
A Django management command to bundle our media.

This command should be integrated into any build or deploy process used with
the project.
"""

from django.core.management.base import NoArgsCommand

from media_bundler import bundler
from media_bundler.jsmin import jsmin
from media_bundler.cssmin import minify_css


def concatenate_files(paths):
    """Generate the contents of several files in 8K blocks."""
    for path in paths:
        with open(path) as input:
            buffer = input.read(8192)
            while buffer:
                yield buffer
                buffer = input.read(8192)
        #yield "\n"


class Command(NoArgsCommand):

    """Bundles your media as specified in settings.py."""

    def handle_noargs(self, **options):
        for bundle in bundler.get_bundles().itervalues():
            self.do_bundle(bundle)

    def do_bundle(self, bundle):
        if bundle.type == "javascript":
            self.do_text_bundle(bundle, jsmin)
        elif bundle.type == "css":
            self.do_text_bundle(bundle, minify_css)
        elif bundle.type == "sprite":
            msg = "Image spriting is not yet implemented."
            raise NotImplementedError(msg)
        else:
            raise bundler.InvalidBundleType(self.type)

    def do_text_bundle(self, bundle, minifier):
        with open(bundle.get_bundle_path(), 'w') as output:
            generator = concatenate_files(bundle.get_paths())
            if bundle.minify:
                # Eventually we should use generators to concatenate and minify
                # things one bit at a time, but for now we use strings.
                output.write(minifier("".join(generator)))
            else:
                output.write("".join(generator))
