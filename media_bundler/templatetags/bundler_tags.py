# media_bundler/templatetags/bundler_tags.py

"""
Template tags for the django media bundler.
"""

from django import template
from django.template import Variable

from media_bundler import bundler
from media_bundler.conf import bundler_settings

register = template.Library()


def context_set_default(context, key, default):
    """Like setdefault for Contexts, only we use the root Context dict."""
    if context.has_key(key):
        return context[key]
    else:
        # Set the value on the root context so our value isn't popped off.
        context.dicts[-1][key] = default
        return default


def bundle_tag(tag_func):
    def new_tag_func(parser, token):
        try:
            tag_name, bundle_name, file_name = token.split_contents()
        except ValueError:
            tag_name = token.contents.split()[0]
            msg = "%r tag takes two arguments: bundle_name and file_name."
            raise template.TemplateSyntaxError(msg % tag_name)
        bundle_name_var = Variable(bundle_name)
        file_name_var = Variable(file_name)
        return tag_func(bundle_name_var, file_name_var)
    # Hack so that register.tag behaves correctly.
    new_tag_func.__name__ = tag_func.__name__
    return new_tag_func


def resolve_variable(var, context):
    try:
        return var.resolve(context)
    except AttributeError:
        return var


class BundleNode(template.Node):

    """Base class for any nodes that are linking bundles.

    Subclasses must define class variables TAG and CONTEXT_VAR.  They can
    optionally override the method 'really_render(url)' to control tag-specific
    rendering behavior.
    """

    TAG = None

    CONTEXT_VAR = None

    def __init__(self, bundle_name, file_name):
        super(BundleNode, self).__init__()
        self.bundle_name = bundle_name
        self.file_name = file_name

    def render(self, context):
        bundle_name = resolve_variable(self.bundle_name, context)
        file_name = resolve_variable(self.file_name, context)
        bundle = bundler.get_bundles()[bundle_name]
        if file_name not in bundle.files:
            msg = "File %r is not in bundle %r." % (file_name,
                                                    bundle_name)
            raise template.TemplateSyntaxError(msg)
        url_set = context_set_default(context, self.CONTEXT_VAR, set())
        if bundler_settings.USE_BUNDLES:
            url = bundle.get_bundle_url()
        else:
            url = bundle.url + file_name
        if url in url_set:
            return ""  # Don't add a bundle or css url twice.
        else:
            url_set.add(url)
            return self.really_render(context, url, bundle_name, file_name)

    def really_render(self, context, url, bundle_name, file_name):
        """Implement bundle type specific rendering behavior."""
        return self.TAG % url


@register.tag
@bundle_tag
def javascript(bundle_name, script_name):
    """Tag to include JavaScript in the template."""
    return JavascriptNode(bundle_name, script_name)


class JavascriptNode(BundleNode):

    """Add a script tag for a script or its bundle inline or at the bottom."""

    TAG = '<script type="text/javascript" src="%s"></script>'

    CONTEXT_VAR = "_script_urls"

    def __init__(self, bundle_name, script_name):
        super(JavascriptNode, self).__init__(bundle_name, script_name)

    def really_render(self, context, url, bundle_name, file_name):
        content = super(JavascriptNode, self).really_render(context, url,
                bundle_name, file_name)
        if bundler_settings.DEFER_JAVASCRIPT:
            deferred = context_set_default(context, "_deferred_content", [])
            deferred.append(content)
            return ""
        else:
            return content


@register.tag
@bundle_tag
def css(bundle_name, css_name):
    """Tag to include CSS in the template."""
    return CssNode(bundle_name, css_name)


class CssNode(BundleNode):

    """Add link tags for a CSS file or its bundle."""

    TAG = '<link rel="stylesheet" type="text/css" href="%s"/>'

    CONTEXT_VAR = "_css_urls"

    def __init__(self, bundle_name, css_name):
        super(CssNode, self).__init__(bundle_name, css_name)


@register.tag
def defer(parser, token):
    nodelist = parser.parse(('enddefer',))
    parser.delete_first_token()
    return DeferNode(nodelist)


class DeferNode(template.Node):

    """Defer some content until later."""

    def __init__(self, nodelist):
        super(DeferNode, self).__init__()
        self.nodelist = nodelist

    def render(self, context):
        # We render the content in this context so that the scoping rules make
        # sense, ie all variables that seem to be in scope really are.
        content = self.nodelist.render(context)
        if bundler_settings.DEFER_JAVASCRIPT:
            deferred = context_set_default(context, "_deferred_content", [])
            deferred.append(content)
            return ""
        else:
            return content


@register.tag
def deferred_content(parser, token):
    """Tag to load deferred content."""
    return DeferredContentNode()


class DeferredContentNode(template.Node):

    """Add script tags for deferred scripts."""

    def render(self, context):
        return "\n".join(context.get("_deferred_content", ()))


class MultiBundleNode(template.Node):

    """Node loading a complete bundle by name."""

    bundle_type_handlers = {
        "javascript": JavascriptNode,
        "css": CssNode,
    }

    def __init__(self, bundle_name_var, **kwargs):
        self.bundle_name_var = Variable(bundle_name_var)

        for attr_name, attr_value in kwargs.items():
            if hasattr(self, attr_name):
                setattr(self, attr_name, attr_value)

    def render(self, context):
        bundle_name = self.bundle_name_var.resolve(context)
        bundle = bundler.get_bundles()[bundle_name]
        type_handler = self.bundle_type_handlers[bundle.type]

        def process_file(file_name):
            return type_handler(self.bundle_name_var,
                                file_name).render(context)

        tags = [process_file(file_name) for file_name in bundle.files]
        return "\n".join(tags)


@register.tag
def load_bundle(parser, token):
    try:
        tag_name, bundle_name = token.split_contents()
    except ValueError:
        tag_name = token.contents.split()[0]
        msg = "%r tag takes a single argument: bundle_name."
        raise template.TemplateSyntaxError(msg % tag_name)
    return MultiBundleNode(bundle_name)
