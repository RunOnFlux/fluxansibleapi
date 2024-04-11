# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import secrets


def getnewkey() -> str:
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    print(getnewkey())
