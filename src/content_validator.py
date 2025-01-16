import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import yaml
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ContentValidator:
    """Validates file content based on file type and rules."""
    
    def __init__(self):
        self.validators = {
            '.py': self._validate_python,
            '.json': self._validate_json,
            '.yaml': self._validate_yaml,
            '.yml': self._validate_yaml,
            '.md': self._validate_markdown,
            '.txt': self._validate_text
        }

    def validate(self, content: str, file_path: Path) -> ValidationResult:
        """Validate content based on file extension."""
        suffix = file_path.suffix.lower()
        validator = self.validators.get(suffix, self._validate_text)
        return validator(content)

    def _validate_python(self, content: str) -> ValidationResult:
        """Validate Python code content."""
        errors = []
        warnings = []

        # Check for syntax errors
        try:
            compile(content, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
            return ValidationResult(False, errors, warnings)

        # Check for common issues
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for potentially dangerous functions
            if re.search(r'\b(eval|exec|os\.system|subprocess\.call)\b', line):
                warnings.append(f"Line {i}: Use of potentially dangerous function")
            
            # Check line length
            if len(line) > 100:
                warnings.append(f"Line {i}: Line too long ({len(line)} characters)")
            
            # Check for hardcoded credentials
            if re.search(r'\b(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', line, re.I):
                warnings.append(f"Line {i}: Possible hardcoded credential")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_json(self, content: str) -> ValidationResult:
        """Validate JSON content."""
        errors = []
        warnings = []

        try:
            data = json.loads(content)
            
            # Check for common issues
            self._check_dict_recursively(data, warnings, path=[])
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_yaml(self, content: str) -> ValidationResult:
        """Validate YAML content."""
        errors = []
        warnings = []
        
        try:
            # First check if it's valid YAML
            yaml.safe_load(content)
            
            # Check indentation and structure
            lines = content.split('\n')
            prev_indent = 0
            list_indent = None
            in_list = False
            key_indents = []  # Stack of key indentation levels
            
            for i, line in enumerate(lines, 1):
                if not line.strip():  # Skip empty lines
                    continue
                    
                # Check for tabs
                if '\t' in line:
                    errors.append(f"Line {i}: Mixed spaces and tabs found")
                    continue
                
                # Get indentation level
                indent = len(line) - len(line.lstrip())
                
                # Skip lines with no indentation
                if indent == 0:
                    in_list = False
                    list_indent = None
                    key_indents = []
                    continue
                
                # Check if indentation is multiple of 2
                if indent % 2 != 0:
                    errors.append(f"Line {i}: Indentation must be multiple of 2 spaces")
                    continue
                
                # Check if line is a key
                if ':' in line and not line.lstrip().startswith('- '):
                    # If we're going deeper, the previous key's indent becomes our parent
                    if indent > prev_indent:
                        key_indents.append(prev_indent)
                    # If we're going back up, pop indents until we find our level
                    while key_indents and indent <= key_indents[-1]:
                        key_indents.pop()
                    
                    # Check if indentation is more than 2 spaces from parent
                    if key_indents and indent > key_indents[-1] + 2:
                        errors.append(f"Line {i}: Indentation increases by more than 2 spaces")
                    
                    prev_indent = indent
                    in_list = False
                    list_indent = None
                    continue
                
                # Check if line starts a list item
                if line.lstrip().startswith('- '):
                    if not in_list:
                        # First list item should be indented 2 spaces from its parent key
                        parent_indent = key_indents[-1] if key_indents else 0
                        expected_indent = parent_indent + 2
                        
                        if indent > expected_indent:
                            errors.append(f"Line {i}: Indentation increases by more than 2 spaces")
                        elif indent < expected_indent:
                            errors.append(f"Line {i}: List item not properly indented")
                        
                        list_indent = indent
                        in_list = True
                    elif indent != list_indent:
                        errors.append(f"Line {i}: Invalid list item indentation")
                    continue
                
                prev_indent = indent
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except yaml.YAMLError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid YAML: {str(e)}"],
                warnings=warnings
            )

    def _validate_markdown(self, content: str) -> ValidationResult:
        """Validate Markdown content."""
        errors = []
        warnings = []

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for broken link patterns
            if '[](' in line or re.search(r'\[\s*\]\(', line):
                warnings.append(f"Line {i}: Empty link found")
            
            # Check for malformed headers
            if re.match(r'#+[^# ]', line):
                warnings.append(f"Line {i}: Missing space after header #")
            
            # Check for broken links with content
            if re.search(r'\[([^\]]+)\]\(\s*\)', line):
                warnings.append(f"Line {i}: Link with text but no URL")

        return ValidationResult(True, errors, warnings)

    def _validate_text(self, content: str) -> ValidationResult:
        """Validate plain text content."""
        errors = []
        warnings = []

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for non-printable characters
            if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', line):
                warnings.append(f"Line {i}: Contains non-printable characters")
            
            # Check for extremely long lines
            if len(line) > 1000:
                warnings.append(f"Line {i}: Extremely long line ({len(line)} characters)")

        return ValidationResult(True, errors, warnings)

    def _check_dict_recursively(self, data: Any, warnings: List[str], path: List[str]) -> None:
        """Recursively check dictionary for common issues."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = path + [str(key)]
                path_str = '.'.join(new_path)

                # Check for sensitive keys
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                    warnings.append(f"Path {path_str}: Contains sensitive information")

                self._check_dict_recursively(value, warnings, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_dict_recursively(item, warnings, path + [str(i)]) 