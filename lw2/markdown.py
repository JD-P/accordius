import markdown
try:
    from mdx_bleach.extension import BleachExtension
    from mdx_bleach.whitelist import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
except ImportError as e:
    print(e)
try:
    from mdx_pmwiki_tables import pmwiki_tables
except ImportError as e:
    print(e)
    
tags = ALLOWED_TAGS + ["div", "i", "dl",
                       "dt", "dd", "sup",
                       "sub", "table", "th",
                       "tr", "tbody","td",
                       "ul","ol","li"]
ALLOWED_ATTRIBUTES.update({"div":['class="toc"']})
bleach = BleachExtension(tags=tags, )
md = markdown.Markdown(extensions=[
                                   'toc',
                                   'meta',
                                   'def_list',
                                   'superscript',
                                   'subscript',
                                   'mdx_linkify'])
