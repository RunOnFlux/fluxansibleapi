# Path to the flux.yml or another ansible yml file you want
FLUX_PLAYBOOK_PATH = "/home/root/FluxNodeInstall/flux.yml"

# The directory to run ansible-playbook command
WORKING_DIR = "/home/root/FluxNodeInstall"

# The environment you are running in
# If production, requires redis running locally for rate limiting storage
# If development, doesn't require redis
ENV = "production"

# The production location that the redis server is running at
REDIS_SERVER_PROD = "redis://localhost:6379"

# Dictionary of whitelisted api keys with the associated ip address
# You can use /tools/api-key-generator.py to generate keys if you need to
API_KEYS = {
    "api-key-here": "127.0.0.1",  # Localhost
    "api-key-here": "ip-address-here",  # Localhost
}

# List of allowed tags to run with ansible playbook
ALLOWED_TAGS = ["ipcheck"]

# These are a list of allowed inventory
# Called using the -l parameters with ansible-playbook
# nickname ansible_host=0.0.0.0 user=userset n=t0
ALLOWED_PATTERNS = ["nickname"]
