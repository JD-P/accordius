import markdown
import pdb

extensions_list = [
    'toc',
    'meta',
    'def_list']

try:
    from mdx_bleach.extension import BleachExtension
    from mdx_bleach.whitelist import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
except ImportError as e:
    print(e)
try:
    from mdx_pmwiki_tables import pmwiki_tables
except ImportError as e:
    print(e)

try:
    from mdx_superscript import SuperscriptExtension
    extensions_list.append(SuperscriptExtension())
except ImportError as e:
    print(e)

try:
    from mdx_subscript import SubscriptExtension
    extensions_list.append(SubscriptExtension())
except ImportError as e:
    print(e)
    
try:
    from mdx_linkify.mdx_linkify import LinkifyExtension
    extensions_list.append(LinkifyExtension())
except ImportError as e:
    print(e)
    
tags = ALLOWED_TAGS + ["div", "i", "dl",
                       "dt", "dd", "sup",
                       "sub", "table", "th",
                       "tr", "tbody","td",
                       "ul","ol","li"]
ALLOWED_ATTRIBUTES.update({"div":['class="toc"']})
bleach = BleachExtension(tags=tags, )
#extensions_list.append(bleach)
# Disable bleach extension because it's broken
md = markdown.Markdown(extensions=extensions_list)
