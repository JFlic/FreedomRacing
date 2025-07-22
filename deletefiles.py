# This file is for cleaning out  www.freedomracing.com/review/product/view, 
# and /www.freedomracing.com/customer/account/login/referer/ in them because they don't hold any information and just bog down the Database.

import os
import glob

def delete_files_with_pattern(folder_path, pattern="www.freedomracing.com_review_product_list_id"):
    """
    Delete all files in a folder that contain the specified pattern in their filename.
    
    Args:
        folder_path (str): Path to the folder to search in
        pattern (str): Pattern to search for in filenames
    """
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory.")
        return
    
    # Find all files containing the pattern
    search_pattern = os.path.join(folder_path, f"*{pattern}*")
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        print(f"No files found containing '{pattern}' in folder '{folder_path}'")
        return
    
    print(f"Found {len(matching_files)} files containing '{pattern}':")
    for file_path in matching_files:
        print(f"  - {os.path.basename(file_path)}")
    
    # Ask for confirmation
    confirmation = input(f"\nDo you want to delete these {len(matching_files)} files? (y/N): ")
    
    if confirmation.lower() in ['y', 'yes']:
        deleted_count = 0
        failed_count = 0
        
        for file_path in matching_files:
            try:
                os.remove(file_path)
                print(f"✓ Deleted: {os.path.basename(file_path)}")
                deleted_count += 1
            except OSError as e:
                print(f"✗ Failed to delete {os.path.basename(file_path)}: {e}")
                failed_count += 1
        
        print(f"\nSummary:")
        print(f"Successfully deleted: {deleted_count} files")
        if failed_count > 0:
            print(f"Failed to delete: {failed_count} files")
    else:
        print("Operation cancelled.")

def main():
    # You can modify this path or make it interactive
    folder_path = "freedomracingdata_filtered"
    
    # Remove quotes if user wrapped path in quotes
    if folder_path.startswith('"') and folder_path.endswith('"'):
        folder_path = folder_path[1:-1]
    elif folder_path.startswith("'") and folder_path.endswith("'"):
        folder_path = folder_path[1:-1]
    
    # Use current directory if no path provided
    if not folder_path:
        folder_path = os.getcwd()
        print(f"Using current directory: {folder_path}")
    
    delete_files_with_pattern(folder_path,"www.freedomracing.com_review_product_view")

if __name__ == "__main__":
    main()