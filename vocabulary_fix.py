#!/usr/bin/env python3
"""
This script fixes the type hint in vocabulary.py to be compatible with Python versions before 3.10.
"""
import os
import sys
import re

def fix_vocabulary_file():
    """
    Replace 'str | URIRef' with 'Union[str, URIRef]' in the vocabulary.py file.
    """
    file_path = os.path.join('src', 'verbalizer', 'vocabulary.py')
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the file already has the imports we need
    if 'from typing import Union' not in content:
        # Add Union import if it's not already there
        content = re.sub(
            r'(from typing import .*)',
            r'\1, Union',
            content
        )
        if 'from typing import ' not in content:
            # If no typing import exists, add it
            content = 'from typing import Union\n' + content
    
    # Replace the type hint
    content = re.sub(
        r'def should_ignore\(self, uri: str \| URIRef\)',
        r'def should_ignore(self, uri: Union[str, URIRef])',
        content
    )
    
    # Write the file back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Successfully updated {file_path} for Python compatibility.")
    return True

if __name__ == "__main__":
    fix_vocabulary_file() 