import subprocess

# Define the base variables
installation_folder = "/data/mapbender/tools/"
default_gui_name = "Geoportal-Hessen-2019"
user_id = "3"
service_type = "wfs"
wms_list_file = "/data/GeoPortal.rlp/useroperations/wfs_list.txt"

# Function to read WMS URLs from a file
def read_wms_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Function to register a WMS service
def register_wms(url):
    register_cmd = f"/usr/bin/php -f {installation_folder}registerOwsCli.php userId={user_id} guiId='{default_gui_name}' serviceType='{service_type}' serviceAccessUrl='{url}'"
    process = subprocess.run(register_cmd, shell=True, capture_output=True, text=True)
    if process.returncode == 0:
        print(f"Successfully registered WMS: {url}")
    else:
        print(f"Failed to register WMS: {url}\nError: {process.stderr}")

# Main process
def main():
    wms_urls = read_wms_urls(wms_list_file)
    for url in wms_urls:
        register_wms(url)

if __name__ == "__main__":
    main()