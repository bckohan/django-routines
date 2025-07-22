import typing as t
from sphinx.ext.autodoc import AttributeDocumenter
from sphinx.ext.autodoc.directive import AutodocDirective
from docutils.parsers.rst import directives
from docutils.nodes import Text, Node
from sphinx import addnodes
from sphinx.domains.python import PyAttribute
from sphinx.util.docutils import SphinxDirective


class AutoSettingDocumenter(AttributeDocumenter):
    """
    Custom autodoc directive that behaves like autoattribute but
    displays only the attribute name (not the full dotted path)
    and preserves type hints.
    """

    objtype = 'setting'
    directivetype = "key"
    priority = AttributeDocumenter.priority + 1
    option_spec = {
        **AttributeDocumenter.option_spec,
        "keyname": directives.unchanged
    }

    def add_directive_header(self, sig):
        self.modname = ""
        super().add_directive_header(sig)
        keyname = self.options.get("keyname", None)
        self.add_line(
            f'   :keyname: {keyname or self.objpath[-1]}',
            self.get_sourcename()
        )


class PyDictKey(PyAttribute):

    option_spec = {
        **PyAttribute.option_spec,
        'keyname': directives.unchanged,
    }

    def handle_signature(self, sig, signode):
        fullname, prefix = super().handle_signature(sig, signode)
        keyname = self.options.get('keyname', None)
        if keyname:
            keyname = keyname.strip('"').strip("'").strip()
            keyname = f'"{keyname}"'
            for addname in signode.traverse(addnodes.desc_addname):
                signode.remove(addname)
            for desc in signode.traverse(addnodes.desc_name):
                for txt in desc.traverse(Text):
                    desc.replace(txt, Text(keyname))
        return fullname, prefix


def setup(app):
    app.add_directive('py:key', PyDictKey)
    app.add_autodocumenter(AutoSettingDocumenter)
    app.add_directive('autosetting', AutodocDirective)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
