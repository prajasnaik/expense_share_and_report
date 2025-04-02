import re

class ParserError(Exception):
    """Custom exception for parser errors."""
    pass

class Parser:
    def __init__(self):
        self.command_pattern = re.compile(r"(\w+)(?:\s+(.*))?")

    def parse(self, input_string):
        match = self.command_pattern.match(input_string)
        if not match:
            raise ParserError("Invalid command format.")
        
        command = match.group(1)
        args = match.group(2).split() if match.group(2) else []
        return command, args