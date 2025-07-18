import os
import shutil
from pathlib import Path

def find_file_in_directory(filename, search_dir):
    """
    Recursively search for a file by name in a directory structure.
    Returns the full path if found, None otherwise.
    """
    for root, dirs, files in os.walk(search_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

def copy_template_to_destination(template_dir="wallet/template", destination_dir="wallet/destination"):
    """
    Copy files from flat template directory to corresponding locations in destination structure.
    
    Args:
        template_dir (str): Path to the flat template directory
        destination_dir (str): Path to the nested destination directory
    """
    # Check if directories exist
    if not os.path.exists(template_dir):
        print(f"Error: Template directory '{template_dir}' does not exist.")
        return
    
    if not os.path.exists(destination_dir):
        print(f"Error: Destination directory '{destination_dir}' does not exist.")
        return
    
    # Get all files from template directory (only files, not subdirectories)
    template_files = [f for f in os.listdir(template_dir) 
                     if os.path.isfile(os.path.join(template_dir, f))]
    
    if not template_files:
        print(f"No files found in template directory '{template_dir}'.")
        return
    
    print(f"Found {len(template_files)} files in template directory:")
    for file in template_files:
        print(f"  - {file}")
    print()
    
    copied_count = 0
    not_found_count = 0
    
    # Process each template file
    for filename in template_files:
        template_file_path = os.path.join(template_dir, filename)
        
        # Find corresponding file in destination structure
        destination_file_path = find_file_in_directory(filename, destination_dir)
        
        if destination_file_path:
            try:
                # Create backup of original file (optional)
                backup_path = destination_file_path + ".backup"
                if os.path.exists(destination_file_path):
                    shutil.copy2(destination_file_path, backup_path)
                    print(f"Created backup: {backup_path}")
                
                # Copy template file to destination
                shutil.copy2(template_file_path, destination_file_path)
                print(f"✓ Copied '{filename}' to '{destination_file_path}'")
                copied_count += 1
                
            except Exception as e:
                print(f"✗ Error copying '{filename}': {e}")
        else:
            print(f"✗ File '{filename}' not found in destination structure")
            not_found_count += 1
    
    print(f"\nSummary:")
    print(f"  Files copied: {copied_count}")
    print(f"  Files not found: {not_found_count}")
    print(f"  Total template files: {len(template_files)}")

def preview_copy_operations(template_dir="wallet/template", destination_dir="wallet"):
    """
    Preview what files would be copied without actually copying them.
    """
    print("PREVIEW MODE - No files will be copied")
    print("=" * 50)
    
    if not os.path.exists(template_dir):
        print(f"Error: Template directory '{template_dir}' does not exist.")
        return
    
    if not os.path.exists(destination_dir):
        print(f"Error: Destination directory '{destination_dir}' does not exist.")
        return
    
    template_files = [f for f in os.listdir(template_dir) 
                     if os.path.isfile(os.path.join(template_dir, f))]
    
    print(f"Template files to process: {len(template_files)}")
    print()
    
    for filename in template_files:
        template_file_path = os.path.join(template_dir, filename)
        destination_file_path = find_file_in_directory(filename, destination_dir)
        
        if destination_file_path:
            print(f"✓ {filename}")
            print(f"  FROM: {template_file_path}")
            print(f"  TO:   {destination_file_path}")
        else:
            print(f"✗ {filename} - NOT FOUND in destination structure")
        print()

if __name__ == "__main__":
    # Uncomment the line below to preview operations first
    #preview_copy_operations(template_dir="conf/dbwallet", destination_dir="wallet")
    
    # Run the actual copy operation
    copy_template_to_destination(template_dir="conf/dbwallet", destination_dir="wallet")