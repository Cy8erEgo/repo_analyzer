import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL of the repository being analyzed")
    parser.add_argument("--date-from", "-s", help="Start date of the analyzed time period (format: YYYY-MM-DD)")
    parser.add_argument("--date-to", "-e", help="End date of the analyzed time period (format: YYYY-MM-DD)")
    parser.add_argument("--branch", "-b", default="master", help="Branch name")
    args = parser.parse_args()

    return args
