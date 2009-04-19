# media_bundler/conf/bundler_settings.py

"""
media_bundler specific settings with the defaults filled in.

If the user has overridden a setting in their settings module, we'll use that
value, but otherwise we'll fall back on the value from
media_bundler.default_settings.  All bundler- specific settings checks should
go through this module, but to check global Django settings, use the normal
django.conf.settings module.
"""

from django.conf import settings

from media_bundler.conf import default_settings


USE_BUNDLES = getattr(settings, "USE_BUNDLES",
                      default_settings.USE_BUNDLES)
DEFER_JAVASCRIPT = getattr(settings, "DEFER_JAVASCRIPT",
                           default_settings.DEFER_JAVASCRIPT)
MEDIA_BUNDLES = getattr(settings, "MEDIA_BUNDLES",
                        default_settings.MEDIA_BUNDLES)
BUNDLE_VERSION_FILE = getattr(settings, "BUNDLE_VERSION_FILE",
                              default_settings.BUNDLE_VERSION_FILE)
BUNDLE_VERSIONER = getattr(settings, "BUNDLE_VERSIONER",
                           default_settings.BUNDLE_VERSIONER)
