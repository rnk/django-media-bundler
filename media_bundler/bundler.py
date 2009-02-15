# media_bundler/bundle.py

from __future__ import with_statement

import math
import os
import shutil
import subprocess
import re
from StringIO import StringIO

from media_bundler import bundler_settings
from media_bundler.bin_packing import Box, pack_boxes
from media_bundler.jsmin import jsmin
from media_bundler.cssmin import minify_css

_BUNDLES = None


class InvalidBundleType(Exception):

    def __init__(self, type):
        msg = "Invalid bundle type: '%s'" % self.type
        super(InvalidBundleType, self).__init__(msg)


def concatenate_files(paths):
    """Generate the contents of several files in 8K blocks."""
    for path in paths:
        with open(path) as input:
            buffer = input.read(8192)
            while buffer:
                yield buffer
                buffer = input.read(8192)


class Bundle(object):

    def __init__(self, name, path, url, files):
        self.name = name
        self.path = path
        self.url = url
        if not url.endswith("/"):
            raise ValueError("Bundle URLs must end with a '/'.")
        self.files = files

    @classmethod
    def check_attr(cls, attrs, attr):
        errmsg = "Invalid bundle: %r attribute %r required." % (attrs, attr)
        assert attr in attrs, errmsg

    @classmethod
    def from_dict(cls, attrs):
        for attr in ("type", "name", "path", "url", "files"):
            cls.check_attr(attrs, attr)
        if attrs["type"] == "javascript":
            return JavascriptBundle(attrs["name"], attrs["path"], attrs["url"],
                                    attrs["files"], attrs.get("minify", False))
        elif attrs["type"] == "css":
            return CssBundle(attrs["name"], attrs["path"], attrs["url"],
                             attrs["files"], attrs.get("minify", False))
        elif attrs["type"] == "png-sprite":
            cls.check_attr(attrs, "css_file")
            return PngSpriteBundle(attrs["name"], attrs["path"], attrs["url"],
                                   attrs["files"], attrs["css_file"])
        else:
            raise InvalidBundleType

    def get_paths(self):
        return [os.path.join(self.path, f) for f in self.files]

    def get_extension(self):
        raise NotImplementedError

    def get_bundle_path(self):
        path = self.name + self.get_extension()
        return os.path.join(self.path, path)

    def get_bundle_url(self):
        url = self.name + self.get_extension()
        return self.url + url

    def make_bundle(self):
        raise NotImplementedError

    def do_text_bundle(self, minifier=None):
        with open(self.get_bundle_path(), "w") as output:
            generator = concatenate_files(self.get_paths())
            if minifier:
                # Eventually we should use generators to concatenate and minify
                # things one bit at a time, but for now we use strings.
                output.write(minifier("".join(generator)))
            else:
                output.write("".join(generator))


class JavascriptBundle(Bundle):

    def __init__(self, name, path, url, files, minify):
        super(JavascriptBundle, self).__init__(name, path, url, files)
        self.minify = minify

    def get_extension(self):
        return ".js"

    def make_bundle(self):
        minifier = jsmin if self.minify else None
        self.do_text_bundle(minifier)


class CssBundle(Bundle):

    def __init__(self, name, path, url, files, minify):
        super(CssBundle, self).__init__(name, path, url, files)
        self.minify = minify

    def get_extension(self):
        return ".css"

    def make_bundle(self):
        minifier = minify_css if self.minify else None
        self.do_text_bundle(minifier)


class PngSpriteBundle(Bundle):

    def __init__(self, name, path, url, files, css_file):
        super(PngSpriteBundle, self).__init__(name, path, url, files)
        self.css_file = css_file

    def get_extension(self):
        return ".png"

    def make_bundle(self):
        import Image  # If this fails, you need the Python Imaging Library.
        boxes = [ImageBox(Image.open(path), path) for path in self.get_paths()]
        # Pick a max_width so that the sprite is squarish and a multiple of 16,
        # and so no image is too wide to fit.
        total_area = sum(box.width * box.height for box in boxes)
        width = max(max(box.width for box in boxes),
                    (int(math.sqrt(total_area)) // 16 + 1) * 16)
        (_, height, packing) = pack_boxes(boxes, width)
        sprite = Image.new("RGBA", (width, height))
        with open(self.css_file, "w") as css:
            css.write("/* Generated classes for django-media-bundler sprites.  "
                      "Don't edit! */\n")
            props = {
                "background-image": "url('%s')" % self.get_bundle_url(),
            }
            css.write(self.make_css(None, props))
            for (left, top, box) in packing:
                # This is a bit of magic to make the transparencies work.  To
                # preserve transparency, we pass the image so it can take its
                # alpha channel mask or something.  However, if the image has no
                # alpha channels, then it fails, we we have to check if the
                # image is RGBA here.
                img = box.image
                mask = img if img.mode == "RGBA" else None
                sprite.paste(img, (left, top), mask)
                props = {
                    "background-position": "%dpx %dpx" % (-left, -top),
                    "width": "%dpx" % box.width,
                    "height": "%dpx" % box.height,
                }
                css.write(self.make_css(os.path.basename(box.filename), props))
        sprite.save(self.get_bundle_path(), "PNG")
        self._optimize_output()

    def _optimize_output(self):
        """Optimize the PNG with pngcrush."""
        sprite_path = self.get_bundle_path()
        tmp_path = sprite_path + '.tmp'
        args = ['pngcrush', '-rem', 'alla', sprite_path, tmp_path]
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        proc.wait()
        if proc.returncode != 0:
            raise Exception('pngcrush returned error code: %r\nOutput was:\n\n'
                            '%s' % (proc.returncode, proc.stdout.read()))
        shutil.move(tmp_path, sprite_path)

    CSS_REGEXP = re.compile(r"[^a-zA-Z\-_]")

    def css_class_name(self, rule_name):
        name = self.name
        if rule_name:
            name += "-" + rule_name
        name = name.replace(" ", "-").replace(".", "-")
        return self.CSS_REGEXP.sub("", name)

    def make_css(self, name, props):
        # We try to format it nicely here in case the user actually looks at it.
        # If he wants it small, he'll bundle it up in his CssBundle.
        css_class = self.css_class_name(name)
        css_propstr = "".join("     %s: %s;\n" % p for p in props.iteritems())
        return "\n.%s {\n%s}\n" % (css_class, css_propstr)


class ImageBox(Box):

    def __init__(self, image, filename):
        (width, height) = image.size
        super(ImageBox, self).__init__(width, height)
        self.image = image
        self.filename = filename


def get_bundles():
    global _BUNDLES
    if not _BUNDLES:
        _BUNDLES = dict((bundle["name"], Bundle.from_dict(bundle))
                        for bundle in bundler_settings.MEDIA_BUNDLES)
    return _BUNDLES
