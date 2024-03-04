import os
import shutil
import subprocess
import sys
from zipfile import ZipFile
from urllib.request import urlopen

def download_and_extract_repo(repo_name):
    # Download the repository zip file
    url = f"https://github.com/cpi-utility/{repo_name}/archive/main.zip"
    with urlopen(url) as response, open("repo.zip", "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    
    # Extract the zip file
    with ZipFile("repo.zip", "r") as zip_ref:
        zip_ref.extractall()

    # Get the extracted folder name
    extracted_folder_name = os.path.commonprefix(zip_ref.namelist()).rstrip('/')

    # Copy files to the root folder with force overwrite
    for root, dirs, files in os.walk(extracted_folder_name):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(os.getcwd(), file)
            shutil.copy2(src_file, dest_file)

    # Clean up
    os.remove("repo.zip")
    shutil.rmtree(extracted_folder_name)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <repository_name>")
        return
    
    repo_name = sys.argv[1]
    
    try:
        download_and_extract_repo(repo_name)
        print("Done!")
        subprocess.run(["python", "main.py"])
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
