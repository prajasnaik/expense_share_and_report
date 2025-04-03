import re

class ParserError(Exception):
    """Custom exception for parser errors."""
    pass

class Parser:
    def parse(self, input_string):
        # This pattern matches either a double-quoted token (capturing its content)
        # or a non-space sequence.
        token_pattern = re.compile(r'"((?:\\.|[^"\\])*)"|(\S+)')
        tokens = []
        for match in token_pattern.finditer(input_string):
            if match.group(1) is not None:
                # Unescape any character preceded by a backslash.
                token = re.sub(r'\\(.)', r'\1', match.group(1))
            else:
                token = match.group(2)
            tokens.append(token)
        
        if not tokens:
            raise ParserError("Invalid command format.")
        
        command = tokens[0]
        args = tokens[1:]
        return command, args