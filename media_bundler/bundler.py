# media_bundler/bundle.py

from __future__ import with_statement

import math
import os
import shutil
import subprocess
import re
from StringIO import StringIO

from media_bundler.conf import bundler_settings
from media_bundler.bin_packing import Box, pack_boxes
from media_bundler.jsmin import jsmin
from media_bundler.cssmin import minify_css
from media_bundler import versioning


class InvalidBundleType(Exception):

    def __init__(self, type_):
        msg = "Invalid bundle type: %r" % type_
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

    """Base class for a bundle of media files.

    A bundle is a collection of related static files that can be concatenated
    together and served as a single file to improve performance.
    """

    def __init__(self, name, path, url, files, type):
        self.name = name
        self.path = path
        self.url = url
        if not url.endswith("/"):
            raise ValueError("Bundle URLs must end with a '/'.")
        self.files = files
        self.type = type

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
                                    attrs["files"], attrs["type"],
                                    attrs.get("minify", False))
        elif attrs["type"] == "css":
            return CssBundle(attrs["name"], attrs["path"], attrs["url"],
                             attrs["files"], attrs["type"],
                             attrs.get("minify", False))
        elif attrs["type"] == "png-sprite":
            cls.check_attr(attrs, "css_file")
            return PngSpriteBundle(attrs["name"], attrs["path"], attrs["url"],
                                   attrs["files"], attrs["type"],
                                   attrs["css_file"])
        else:
            raise InvalidBundleType(attrs["type"])

    def get_paths(self):
        return [os.path.join(self.path, f) for f in self.files]

    def get_extension(self):
        raise NotImplementedError

    def get_bundle_filename(self):
        return self.name + self.get_extension()

    def get_bundle_path(self):
        filename = self.get_bundle_filename()
        return os.path.join(self.path, filename)

    def get_bundle_url(self):
        unversioned = self.get_bundle_filename()
        filename = versioning.get_bundle_versions().get(self.name, unversioned)
        return self.url + filename

    def make_bundle(self, versioner):
        self._make_bundle()
        if versioner:
            versioner.update_bundle_version(self)

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

    """Bundle for JavaScript."""

    def __init__(self, name, path, url, files, type, minify):
        super(JavascriptBundle, self).__init__(name, path, url, files, type)
        self.minify = minify

    def get_extension(self):
        return ".js"

    def _make_bundle(self):
        minifier = jsmin if self.minify else None
        self.do_text_bundle(minifier)


class CssBundle(Bundle):

    """Bundle for CSS."""

    def __init__(self, name, path, url, files, type, minify):
        super(CssBundle, self).__init__(name, path, url, files, type)
        self.minify = minify

    def get_extension(self):
        return ".css"

    def _make_bundle(self):
        minifier = minify_css if self.minify else None
        self.do_text_bundle(minifier)


class PngSpriteBundle(Bundle):

    """Bundle for PNG sprites.

    In addition to generating a PNG sprite, it also generates CSS rules so that
    the user can easily place their sprites.  We build sprite bundles before CSS
    bundles so that the user can bundle the generated CSS with the rest of their
    CSS.
    """

    def __init__(self, name, path, url, files, type, css_file):
        super(PngSpriteBundle, self).__init__(name, path, url, files, type)
        self.css_file = css_file

    def get_extension(self):
        return ".png"

    def make_bundle(self, versioner):
        import Image  # If this fails, you need the Python Imaging Library.
        boxes = [ImageBox(Image.open(path), path) for path in self.get_paths()]
        # Pick a max_width so that the sprite is squarish and a multiple of 16,
        # and so no image is too wide to fit.
        total_area = sum(box.width * box.height for box in boxes)
        width = max(max(box.width for box in boxes),
                    (int(math.sqrt(total_area)) // 16 + 1) * 16)
        (_, height, packing) = pack_boxes(boxes, width)
        sprite = Image.new("RGBA", (width, height))
        for (left, top, box) in packing:
            # This is a bit of magic to make the transparencies work.  To
            # preserve transparency, we pass the image so it can take its
            # alpha channel mask or something.  However, if the image has no
            # alpha channels, then it fails, we we have to check if the
            # image is RGBA here.
            img = box.image
            mask = img if img.mode == "RGBA" else None
            sprite.paste(img, (left, top), mask)
        sprite.save(self.get_bundle_path(), "PNG")
        self._optimize_output()
        # It's *REALLY* important that this happen here instead of after the
        # generate_css() call, because if we waited, the CSS woudl have the URL
        # of the last version of this bundle.
        if versioner:
            versioner.update_bundle_version(self)
        self.generate_css(packing)

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

    def generate_css(self, packing):
        """Generate the background offset CSS rules."""
        with open(self.css_file, "w") as css:
            css.write("/* Generated classes for django-media-bundler sprites.  "
                      "Don't edit! */\n")
            props = {
                "background-image": "url('%s')" % self.get_bundle_url(),
            }
            css.write(self.make_css(None, props))
            for (left, top, box) in packing:
                props = {
                    "background-position": "%dpx %dpx" % (-left, -top),
                    "width": "%dpx" % box.width,
                    "height": "%dpx" % box.height,
                }
                css.write(self.make_css(os.path.basename(box.filename), props))

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

    """A Box representing an image.

    We hand these off to the bin packing algorithm.  After the boxes have been
    arranged, we can place the associated image in the sprite.
    """

    def __init__(self, image, filename):
        (width, height) = image.size
        super(ImageBox, self).__init__(width, height)
        self.image = image
        self.filename = filename

    def __repr__(self):
        return "<ImageBox: filename=%r image=%r>" % (self.filename, self.image)


_bundles = None

def get_bundles():
    """Return a dict of bundle names and bundles as described in settings.py.

    The result of this function is cached, because settings should never change
    throughout the execution of the program.
    """
    global _bundles
    if not _bundles:
        _bundles = dict((bundle["name"], Bundle.from_dict(bundle))
                        for bundle in bundler_settings.MEDIA_BUNDLES)
    return _bundles
