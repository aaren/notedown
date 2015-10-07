import re

from mistune import BlockLexer


class AttributesLexer(BlockLexer):

    def enable_attributes(self):
	"""Modify mistunes fence matching regex to allow
	arbitrary attributes.
        """
	self.rules.fences = re.compile(
		r'^ *(`{3,}|~{3,}) *(.+)? *\n'  # ```{.lang .whatever}
		r'([\s\S]+?)\s*'
		r'\1 *(?:\n+|$)'  # ```
		)

lexer = AttributesLexer()

with open('attributes.md') as f:
    md = f.read()

for token in lexer.parse(md):
    print token

print '---------'

lexer.enable_attributes()

for token in lexer.parse(md):
    print token
