# media_bundler/bundle.py

import os

from media_bundler import bundler_settings

_BUNDLES = None


class InvalidBundleType(Exception):

    def __init__(self, type):
        msg = "Invalid bundle type: '%s'" % self.type
        super(InvalidBundleType, self).__init__(msg)


class Bundle(object):

    def __init__(self, type, name, path, url, files, minify):
        self.type = type
        self.name = name
        self.path = path
        self.url = url
        if not url.endswith("/"):
            raise ValueError("Bundle URLs must end with a '/'.")
        self.files = files
        self.minify = minify

    def get_paths(self):
        return [os.path.join(self.path, f) for f in self.files]

    def get_extension(self):
        if self.type == "javascript":
            return ".js"
        elif self.type == "css":
            return ".css"
        elif self.type == "sprite":
            return ".png"
        else:
            raise InvalidBundleType(self.type)

    def get_bundle_path(self):
        path = self.name + self.get_extension()
        return os.path.join(self.path, path)

    def get_bundle_url(self):
        url = self.name + self.get_extension()
        return self.url + url

    @classmethod
    def from_dict(cls, attrs):
        return cls(attrs["type"], attrs["name"], attrs["path"], attrs["url"],
                   attrs["files"], attrs["minify"])


def get_bundles():
    global _BUNDLES
    if not _BUNDLES:
        _BUNDLES = dict((bundle['name'], Bundle.from_dict(bundle))
                        for bundle in bundler_settings.MEDIA_BUNDLES)
    return _BUNDLES
