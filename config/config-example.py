# Path to the flux.yml or another ansible yml file you want
FLUX_PLAYBOOK_PATH = "/home/root/FluxNodeInstall/flux.yml"
SSHSETUP_PLAYBOOK_PATH = "/home/root/FluxNodeInstall/playbooks/ssh_setup.yml"

# Set a default playbook, this will be used if no playbook is passed in via api
DEFAULT_PLAYBOOK = FLUX_PLAYBOOK_PATH
ALLOW_DEFAULT_PLAYBOOK = True  # If false playbooks must be passed through via api

# List of allowed playbooks to run by keyword
ALLOWED_PLAYBOOKS = {
    "flux": FLUX_PLAYBOOK_PATH,
    "ssh_setup": SSHSETUP_PLAYBOOK_PATH,
}

# The directory to run ansible-playbook command
WORKING_DIR = "/home/root/FluxNodeInstall"

# The environment you are running in
# If production, requires redis running locally for rate limiting storage
# If development, doesn't require redis
ENV = "production"

# The production location that the redis server is running at
REDIS_SERVER_PROD = "redis://localhost:6379"

# Dictionary of whitelisted api keys with the associated ip address, tags, patterns available to each api key
# You can use /tools/api-key-generator.py to generate keys if you need to
API_KEYS = {
    "api-key-here": {
        "whitelisted_ipaddress": "127.0.0.1",  # Localhost
        "whitelisted_tags": {"all"},
        "whitelisted_patterns": {"all"},
    },
    "api-key-here": {
        "whitelisted_ipaddress": "ip-address-here",
        "whitelisted_tags": {"ipcheck"},
        "whitelisted_patterns": {"nickname"},
    },
}

# List of allowed tags to run with ansible playbook
ALLOWED_TAGS = ["ipcheck"]

# These are a list of allowed inventory
# Called using the -l parameters with ansible-playbook
# nickname ansible_host=0.0.0.0 user=userset n=t0
ALLOWED_PATTERNS = ["nickname"]
