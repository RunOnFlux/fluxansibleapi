### This file is a part of .gitignore
### Any changes to this file shouldn't be commited to github

# Path to the flux.yml or another ansible yml file you want
FLUX_PLAYBOOK_PATH = ''

# The directory to run ansible-playbook command
WORKING_DIR = ''

# Dictionary of whitelisted api keys with the associated ip address 
# You can use /tools/api-key-generator.py to generate keys if you need to 
API_KEYS = {
}

# List of allowed tags to run with ansible playbook
ALLOWED_TAGS = [
]

# These are a list of allowed inventory
# Called using the -l parameters with ansible-playbook
# nickname ansible_host=0.0.0.0 user=userset n=t0
ALLOWED_PATTERNS = [
]