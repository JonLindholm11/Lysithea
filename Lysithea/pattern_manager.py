# lysithea/pattern_manager.py

import re

"""
Pattern file management - loading, listing, and mapping operations to patterns
"""

from pathlib import Path

def get_pattern_metadata(pattern_path):
    """Extract metadata from pattern file"""
    pattern_content = load_pattern(pattern_path)
    if not pattern_content:
        return None
    
    # Extract @output-dir (default: output)
    output_dir_match = re.search(r'@output-dir\s+(.+)', pattern_content)
    output_dir = output_dir_match.group(1).strip() if output_dir_match else 'output'
    
    # Extract @file-naming (default: {resource}.js)
    file_naming_match = re.search(r'@file-naming\s+(.+)', pattern_content)
    file_naming = file_naming_match.group(1).strip() if file_naming_match else '{resource}.js'
    
    return {
        'output_dir': output_dir,
        'file_naming': file_naming
    }

def load_pattern(pattern_path):
    """Load a pattern file"""
    full_path = Path('..') / 'patterns' / pattern_path
    if not full_path.exists():
        return None
    return full_path.read_text()

def list_available_patterns():
    """Get list of all available patterns"""
    pattern_dir = Path('..') / 'patterns'
    if not pattern_dir.exists():
        return []
    
    patterns = []
    for pattern_file in pattern_dir.rglob('*.js'):
        relative_path = pattern_file.relative_to(pattern_dir)
        patterns.append(str(relative_path))
    
    return patterns

def map_operation_to_pattern(operation):
    """Map operation name to pattern file"""
    op_lower = operation.lower()
    
    # Check for GET by ID first (most specific)
    if 'get' in op_lower and ('by id' in op_lower or 'by-id' in op_lower):
        return 'javascript/express/routes/get-users-by-id-auth.js'
    
    # Check for GET by ANY attribute (price, category, etc.)
    elif 'get' in op_lower and 'by' in op_lower:
        print(f"  → GET by attribute detected, using GET by ID pattern")
        return 'javascript/express/routes/get-users-by-id-auth.js'
    
    # Generic GET all (MUST come after specific GET checks)
    elif 'get' in op_lower:
        return 'javascript/express/routes/get-users-auth.js'
    
    elif 'post' in op_lower or 'create' in op_lower:
        return 'javascript/express/routes/post-users-auth.js'
    elif 'put' in op_lower or 'update' in op_lower:
        return 'javascript/express/routes/put-user-auth.js'
    elif 'delete' in op_lower or 'remove' in op_lower:
        return 'javascript/express/routes/delete-users-auth.js'
    
    return None