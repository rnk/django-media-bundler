# media_bundler/management/commands/bundle_media.py

"""
A Django management command to bundle our media.

This command should be integrated into any build or deploy process used with
the project.
"""

from django.core.management.base import NoArgsCommand

from media_bundler import bundler


class Command(NoArgsCommand):

    """Bundles your media as specified in settings.py."""

    def handle_noargs(self, **options):
        # We do the image bundles first because they generate CSS that may get
        # bundled by a CssBundle.
        def key(bundle):
            return -int(isinstance(bundle, bundler.PngSpriteBundle))
        bundles = sorted(bundler.get_bundles().itervalues(), key=key)
        for bundle in bundles:
            bundle.make_bundle()
