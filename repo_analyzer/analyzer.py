import os
import re
from collections import defaultdict
import datetime
from typing import List, Tuple, Optional

from repo_analyzer.cli import parse_args
from repo_analyzer.repo import Repository
from repo_analyzer.errors import AnalyzerError


# parse command line arguments
args = parse_args()

# get github credentials from environment variables
GITHUB_AUTH = os.getenv("GITHUB_LOGIN"), os.getenv("GITHUB_TOKEN")

if not all(GITHUB_AUTH):
    raise AnalyzerError("Bad credentials")


class Analyzer:
    __STALE_PULL_REQUESTS_DAYS = 30
    __STALE_ISSUES_DAYS = 14

    def __init__(self, repo_url: str, branch: str = "master", date_from: str = None, date_to: str = None):
        self.__repo_url = repo_url
        self.__date_from = self._parse_time(date_from)
        self.__date_to = self._parse_time(date_to)
        self.__repo_owner, self._repo_name = self._parse_url(repo_url)
        self.__branch = branch

        self.__repo = Repository(
            self.__repo_owner, self._repo_name, self.__branch, auth=GITHUB_AUTH
        )

    @staticmethod
    def _parse_url(repo_url: str) -> List[str]:
        """
        Parses the URL of the repository and returns a list of owner name and project name.
        @param repo_url: repository URL
        @return: list of owner name and project name
        """
        try:
            return re.findall(r"github\.com/([^/]+)/([^\/?]+)", repo_url, re.I)[0]
        except IndexError:
            raise AnalyzerError("Incorrect repository URL")

    @staticmethod
    def _parse_time(time_string: str, source: str = "input") -> Optional[datetime.datetime]:
        """
        Converts a string to datetime depending on the source ("input" or "api").
        @param time_string: time string
        @param source: time string source
        @return: datetime
        """
        if not time_string:
            return None

        format_string = "%Y-%m-%d" if source == "input" else "%Y-%m-%dT%H:%M:%SZ"
        try:
            return datetime.datetime.strptime(time_string, format_string)
        except ValueError:
            raise AnalyzerError("Incorrect date format")

    @staticmethod
    def pprint_contributors(contributors: List[Tuple[str, int]]) -> None:
        """
        Nicely prints the specified list of contributors.
        @param contributors: list of contributors
        @return:
        """
        if not contributors:
            return

        for c in contributors:
            print("{} {}".format(c[0].ljust(50, "_"), c[1]))

    def __filter_by_date(self, date: datetime.datetime) -> bool:
        """
        Checks if the specified date falls within the specified time period (self._date_from, self._date_to).
        @param date: datetime object
        @return: True of False
        """
        if (self.__date_from and date < self.__date_from) or (self.__date_to and date > self.__date_to):
            return False
        return True

    def _summarize(self, elements: List[dict], stale_days: int) -> Tuple[int, int, int]:
        """
        Filters the specified list of items by the specified time (date_from, date_to) and
        and collect statistics on them (opened, closed and stale).
        @param elements: list of some elements received from the Repository class
        @param stale_days: the minimum number of days at which an element can be considered stale
        @return: number of open, closed and stale elements
        """
        opened = 0
        closed = 0
        stale = 0

        deadline = datetime.datetime.now() - datetime.timedelta(days=stale_days)

        for element in elements:
            # filter elements by date
            created_at = self._parse_time(element["created_at"], source="api")

            if not self.__filter_by_date(created_at):
                continue

            # collect statistics
            if element["state"] == "open":
                opened += 1
                if created_at < deadline:
                    stale += 1
            else:
                closed += 1

        return opened, closed, stale

    def get_contributors(self, count: int = 0) -> List[Tuple[str, int]]:
        """
        Gets a list of all (or specified number) contributors and their number of commits.
        @param count: contributors count
        @return: list of contributors and their number of commits
        """
        date_from = self.__date_from.isoformat() + "Z" if self.__date_from else None
        date_to = self.__date_to.isoformat() + "Z" if self.__date_to else None

        # get commits for the specified period of time
        commits = self.__repo.get_commits(date_from, date_to)

        # collect statistics on commits
        rating = defaultdict(int)

        for commit in commits:
            author = commit["author"]

            if not author:
                continue

            rating[author["login"]] += 1

        # sort by the number of commits in descending order
        rating = list(rating.items())
        rating.sort(key=lambda x: x[1], reverse=True)

        if count:
            rating = rating[:count]
        return rating

    def get_pull_requests_stat(self) -> Tuple[int, int, int]:
        """
        Gets statistics on the number of open, closed and stale pull requests for a specified period of time,
        taking into account the specified branch.
        @return: number of open, closed and stale pull requests
        """
        return self._summarize(
            self.__repo.get_pull_requests(), self.__STALE_PULL_REQUESTS_DAYS
        )

    def get_issues_stat(self) -> Tuple[int, int, int]:
        """
        Gets statistics on the number of open, closed and stale issues
        @return: number of open, closed and stale issues
        """
        return self._summarize(self.__repo.get_issues(), self.__STALE_ISSUES_DAYS)


def just(s: str) -> str:
    """
    Aligns the given string to the left in a certain way
    @param s: string
    @return: resulting string
    """
    return s.ljust(50, "_")


def main() -> None:
    """
    Entry point
    @return:
    """
    print("RepoAnalyzer v1.0\nBy @cyberego\n")

    analyzer = Analyzer(args.url, args.branch, date_from=args.date_from, date_to=args.date_to)
    contributors = analyzer.get_contributors(30)

    if contributors:
        print("Top {} contributors".format(len(contributors)))
        analyzer.pprint_contributors(contributors)
    else:
        print("No contributors")

    pull_requests = analyzer.get_pull_requests_stat()

    print()
    print(just("Number of open pull requests:"), pull_requests[0])
    print(just("Number of closed pull requests:"), pull_requests[1])
    print(just("Number of stale pull requests:"), pull_requests[2])

    issues = analyzer.get_issues_stat()

    print()
    print(just("Number of open issues:"), issues[0])
    print(just("Number of closed issues:"), issues[1])
    print(just("Number of stale issues:"), issues[2])
