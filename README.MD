# Flux Ansible API

This is a multithreaded python api that allows simple interaction between users and ansible-playbook.

## Table of Contents

- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Developer Setup](#developer)
- [Production Setup](#production)
- [Api Endpoints](#api)
- [Contributing](#contributing)
- [License](#license)

## About

This api allows users to send api commands which will be directed to ansible-playbook. It includes security measures like IP address whitelisting, and requires API Keys.

## Features

- Multithreaded - Can run multiple ansible-playbook commands from multiple users at the same time
- Inventory Safety - Only one ansible-playbook can be executed on a inventory object at a time. 
- IP Whitelisting - You can whitelist only specific ip to be able to interact with your api
- API Key - You can generate and provide users with API keys which works along side the IP Whitelist. 

## Prerequisites

1. Python3 - https://www.python.org/downloads/

2. Ansible Environment Setup


## Installation

1. `git clone https://github.com/RunOnFlux/fluxansibleapi.git`

2. `cd fluxansibleapi`

3. `pip install -r requirements.txt`

The requried packages that will get installed with requirements.txt are

1. ansible_runner - https://github.com/ansible/ansible-runner
2. Flask - https://flask.palletsprojects.com/en/3.0.x/

## Developer

### Requirements

1. Follow the [Install Instructions](#installation)

2. Certificate and Key created and placed into the keys folder
    - How to create a the key and cert file
        - `openssl genrsa 2048 > host.key`
        - `chmod 400 host.key`
        - `openssl req -new -x509 -nodes -sha256 -days 365 -key host.key -out host.cert`

### Deploy

1. `python3 app.py`

## Production

We will use Gunicorn to run the Flask servers in a production environment.

#### Requirements

1. Complete the [Install Instructions](#installation)

2. Certificate and Key created and placed into the keys folder
    - How to create a the key and cert file
        - `openssl genrsa 2048 > host.key`
        - `chmod 400 host.key`
        - `openssl req -new -x509 -nodes -sha256 -days 365 -key host.key -out host.cert`

3. Gunicorn - ([Install Instructions for your Operating System](https://docs.gunicorn.org/en/stable/install.html))

### Deploy

This command will start the server listening on port 9999. You can change the pathing to your host.cert and host.key files to where they are stored. 

1. `gunicorn -b 0.0.0.0:9999 --certfile=/home/main/FluxNodeInstall/server/keys/host.cert --keyfile=/home/main/FluxNodeInstall/server/keys/host.key app:app`


## API

All requests require the following headers: 
1. `x-api-key`: [Your API key]
2. `Content-Type`: application/json

### /api/

This endpoint is the base endpoint and will let you know if you are whitelisted

#### Request

- **URL**: `/api/
- **Method**: `GET`
- **Headers**:
  - `x-api-key`: [Your API key]

#### Response

- **Status Code**: `200 OK`
- **Body** (JSON):
  ```json
  {
    "message": "This is a whitelisted API endpoint with API key authentication"
  } 

### /api/sendcommand

This endpoint allows sending a command to the server. 

#### Request

- **URL**: `/api/sendcommand`
- **Method**: `POST`
- **Headers**:
  - `x-api-key`: [Your API key]
  - `Content-Type`: application/json
- **Body** (JSON):
  ```json
  {
    "pattern": "value",
    "tags": "tag1"
  }

#### Response

- **Status Code**: `200 OK`
- **Body** (JSON):
  ```json
  {
    "ansible_started_time": "Mon Apr 8 11:49:05 2024",
    "message": "Ansible command execution started.",
    "pattern": "pattern",
    "status": "started",
    "tags": "ipcheck",
    "tracker_event_id": "91543a7e-3d6d-4689-a90f-25d940dcfdf6"
  }

### /api/checkstatus

This endpoint allows you to check on the status on an existing command that was sent using the commands id

#### Request

- **URL**: `/api/checkstatus`
- **Method**: `POST`
- **Headers**:
  - `x-api-key`: [Your API key]
  - `Content-Type`: application/json
- **Body** (JSON):
  ```json
  {
    "tracker_event_id": "91543a7e-3d6d-4689-a90f-25d940dcfdf6"
  }


#### Response

- **Status Code**: `200 OK`
- **Body** (JSON):
  ```json
  {
    "ansible_completed_time": "Mon Apr 8 10:43:52 2024",
    "ansible_started_time": "Mon Apr 8 10:42:50 2024",
    "pattern": "pattern",
    "result": "[Truncated Ansible Output]",
    "status": "completed",
    "tag": "ipcheck"
  }


## Contributing

Feel free to contribute or encourage others to contribute to the project by reporting bugs, suggesting features, or submitting a pull request. 

To submit a pull request please follow this structure: 

1. Fork the repository
2. Create a new branch (`git checkout -b feature/feature-name`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/feature-name`)
6. Create a new Pull Request

## License

This project is licensed under the [MIT License](LICENSE)
