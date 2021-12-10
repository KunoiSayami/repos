import re

signs = [r'\>\=', r'\<\=', r'\=\=', r'\>', r'\<']
signs_or = r'|'.join(signs)
deps_pattern = re.compile(rf'({signs_or}).*')


def depends_strip(deps: str) -> str:
    return deps_pattern.sub('', deps)