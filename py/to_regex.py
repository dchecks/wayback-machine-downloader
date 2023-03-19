import re

class ToRegexMixin:
    REGEXP_DELIMITERS = {
        '%r{': '}',
        '/': '/',
    }
    INLINE_OPTIONS = re.compile(r'[imxnesu]*')

    @staticmethod
    def literal(string):
        return all(not string.startswith(s) and not re.search(r'{}{}'.format(re.escape(e), ToRegexMixin.INLINE_OPTIONS.pattern), string) for s, e in ToRegexMixin.REGEXP_DELIMITERS.items())

    def to_regex(self, string, **options):
        if args := self.as_regexp(string, **options):
            return re.compile(*args)
        return None

    def as_regexp(self, string, literal=None, detect=None, ignore_case=None, multiline=None, extended=None, lang=None):
        if detect and string == '':
            return None

        if literal or (detect and ToRegexMixin.literal(string)):
            content = re.escape(string)
        elif delim_set := next(((k, v) for k, v in ToRegexMixin.REGEXP_DELIMITERS.items() if string.startswith(k)), None):
            delim_start, delim_end = delim_set
            match = re.fullmatch(r'{}(.*){}({})'.format(re.escape(delim_start), re.escape(delim_end), ToRegexMixin.INLINE_OPTIONS.pattern), string, re.UNICODE)
            if match:
                content = match.group(1)
                inline_options = match.group(2)
                content = content.replace('\\/', '/')
                if inline_options:
                    if 'i' in inline_options:
                        ignore_case = True
                    if 'm' in inline_options:
                        multiline = True
                    if 'x' in inline_options:
                        extended = True
                    lang = ''.join(re.findall(r'[nesu]', inline_options, re.IGNORECASE)).lower()
            else:
                return None
        else:
            return None

        flags = 0
        if ignore_case:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if extended:
            flags |= re.VERBOSE

        if lang:
            if lang == 'u':
                return content, flags
            return content, flags, lang
        else:
            return content, flags


to_regex_mixin = ToRegexMixin()

def to_regex(string, **options):
    return to_regex_mixin.to_regex(string, **options)
