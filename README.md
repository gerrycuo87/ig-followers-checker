# ig-followers-checker

This repo contains a Python tool that can be used to extract and compare Instagram follower/following lists. \
It can be packaged by Docker so to run anywhere, with no Python installation required, or by a Jenkins pipeline,
 that builds, tests and ships the tool automatically. \
It is thought for both a non-expert audience (just take the tool and use it) and experts that want tinker with the code,
Jenkinsfile, Dockerfile and so on.

## Table of contents

- [ig-followers-checker](#ig-followers-checker)
  - [Table of contents](#table-of-contents)
  - [Setup](#setup)
    - [Usage with pip](#usage-with-pip)

## Setup

To start using the content of this repo, choose one of the following options.

### Usage with pip

1. Create a virtual environment that uses python3 (e.g. `py -3.xx -m venv venv`) and activate it.
2. Get the necessary modules from `requirements.txt`: open the project folder in a terminal and execute:
`pip install -r requirements.txt`.
3. Run the tool `/src/igfc.py` and enter the required information.
