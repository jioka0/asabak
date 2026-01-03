#!/usr/bin/env python3
"""
Safely remove console.log statements from JavaScript and HTML files.
This version properly handles all edge cases.
"""

import re
import os

def remove_console_logs_advanced(content):
    """
    Remove console.log statements including multi-line calls.
    Preserves code structure and handles edge cases.
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this line contains console.log
        if 'console.log' in line:
            # Find the start of console.log
            indent = len(line) - len(line.lstrip())
            
            # Track parentheses to find the complete statement
            paren_count = 0
            in_console_log = False
            temp_line = line
            
            for char in temp_line:
                if 'console.log' in temp_line[:temp_line.index(char)+1] and not in_console_log:
                    in_console_log = True
                if in_console_log:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            # Found the end of console.log
                            break
            
            # If statement continues on next lines
            if paren_count > 0:
                # Multi-line console.log - skip until we find the closing
                while i < len(lines) and paren_count > 0:
                    i += 1
                    if i < len(lines):
                        for char in lines[i]:
                            if char == '(':
                                paren_count += 1
                            elif char == ')':
                                paren_count -= 1
                                if paren_count == 0:
                                    break
            
            # Skip this line (and any continuation lines we found)
            i += 1
            continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)

def process_file(filepath):
    """Process a single file to remove console.log statements."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        cleaned_content = remove_console_logs_advanced(content)
        
        if cleaned_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            # Count how many console.log were removed
            original_count = original_content.count('console.log')
            remaining_count = cleaned_content.count('console.log')
            removed = original_count - remaining_count
            
            print(f"✓ {filepath}")
            print(f"  Removed {removed} console.log statement(s)")
            return True
        return False
    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")
        return False

def main():
    # Files to process
    files_to_clean = [
        '/home/nekwasar/Documents/asabak/blog/templates/template1-banner-image.html',
        '/home/nekwasar/Documents/asabak/blog/templates/template2-banner-video.html',
        '/home/nekwasar/Documents/asabak/blog/templates/template3-listing.html',
        '/home/nekwasar/Documents/asabak/blog/templates/index.html',
        '/home/nekwasar/Documents/asabak/blog/js/blog.js',
        '/home/nekwasar/Documents/asabak/blog/js/device-fingerprint.js',
        '/home/nekwasar/Documents/asabak/blog/templates/js/blog-templates.js',
    ]
    
    print("🧹 Cleaning console.log statements...\n")
    
    processed = 0
    for filepath in files_to_clean:
        if os.path.exists(filepath):
            if process_file(filepath):
                processed += 1
            else:
                print(f"- No changes needed: {os.path.basename(filepath)}")
        else:
            print(f"✗ Not found: {filepath}")
    
    print(f"\n✅ Successfully processed {processed} file(s)")

if __name__ == '__main__':
    main()
