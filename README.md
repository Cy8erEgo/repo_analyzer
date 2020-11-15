# repo_analyzer
Repository statistics collector

## Installation
Required Python version >= 3.6
1) Install dependencies  
```
poetry install  # install dependencies
poetry shell    # activate the virtual environment
```
Or without Poetry:
```
pip install requests>=2.25.0
```
2) Also you must set the environment variables `GITHUB_LOGIN` and `GITHUB_TOKEN`

## Usage 
```
usage: analyze.py [-h] [--date-from DATE_FROM] [--date-to DATE_TO] [--branch BRANCH] url

positional arguments:
  url                   URL of the repository being analyzed

optional arguments:
  -h, --help            show this help message and exit
  --date-from DATE_FROM, -s DATE_FROM
                        Start date of the analyzed time period (format: YYYY-MM-DD)
  --date-to DATE_TO, -e DATE_TO
                        End date of the analyzed time period (format: YYYY-MM-DD)
  --branch BRANCH, -b BRANCH
                        Branch name (default: master)
```
**Example:**
```bash
python analyze.py https://github.com/smilejay/python -s 2019-06-01 -e 2020-06-01
```

## CI/CD implementation
The implementation builds on using Github Actions. When you create a push to the `issue/*` branch, linting and unit testing are called. If all tests pass, the changes are merged into the master branch. If the merge is successful, the tests are run on the master branch. After that, the Docker image is built and published to the Docker Hub. GitHub notifies the VPS with the deployment server when the Docker image is ready. The deployment server downloads the image from the Docker Hub and runs it.
