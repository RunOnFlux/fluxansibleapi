import datetime
import os


def timestamp_to_datestring(timestamp) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp).strftime("%c")


# Check the ENV is set to production when running with gunicorn
def check_config_gunicorn_production(app):
    if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
        if app.config.get("ENV") != "production":
            raise ValueError(
                "ENV configuration variable must be set to 'production' when running with Gunicorn."
            )


# Check the api keys are the correct keys
def check_config_api_keys(app):
    api_keys = app.config.get("API_KEYS")
    if not api_keys:
        raise ValueError("API_KEYS configuration variable must be set")

    for key, info in api_keys.items():
        if not info.get("whitelisted_ipaddress"):
            raise ValueError(
                f"ApiKey: {key} -> 'whitelisted_ipaddress' configuration variable must be set. Please look at the config/config-example.py"
            )
        if not info.get("whitelisted_tags"):
            raise ValueError(
                f"ApiKey: {key} -> 'whitelisted_tags' configuration variable must be set. Please look at the config/config-example.py"
            )

        if not info.get("whitelisted_patterns"):
            raise ValueError(
                f"ApiKey: {key} -> 'whitelisted_patterns' configuration variable must be set. Please look at the config/config-example.py"
            )


# Check config file directories set, exist, and aren't empty
def check_config_directories(app):
    dir_names = ["FLUX_PLAYBOOK_PATH", "SSHSETUP_PLAYBOOK_PATH", "WORKING_DIR"]

    for name in dir_names:
        dir = app.config.get(name)

        if not dir:
            raise ValueError(f"{name} configuration variable must be set")

        if len(dir) == 0:
            raise ValueError(f"{name} configuration variable can't be empty")

        if not os.path.exists(dir):
            raise ValueError(f"{name} directory path doesn't exist")


def verify_config(app):
    check_config_gunicorn_production(app)
    check_config_api_keys(app)
    check_config_directories(app)
