from typing import List

import requests


class State:
    """
    Constants storing the names of states of pull requests and issues.
    """

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class Sorting:
    """
    Constants storing the names of sorting types of pull requests and issues.
    """

    CREATE = "created"
    UPDATE = "updated"

    class _Base:
        CREATE = "created"
        UPDATE = "updated"

    class Prs(_Base):
        POPULARITY = "popularity"
        LONG_RUNNING = "long-running"

    class Issues(_Base):
        COMMENTS = "comments"


class Repository:
    __headers = {"Accept": "application/vnd.github.v3+json"}
    __page_size = 100

    def __init__(self, username: str, project: str, branch: str = "master", auth=None):
        self._username = username
        self._project = project
        self._branch = branch

        self._auth = auth
        self._base_url = f"https://api.github.com/repos/{username}/{project}"

    @property
    def username(self) -> str:
        return self._username

    @property
    def project(self) -> str:
        return self._project

    @property
    def branch(self) -> str:
        return self._branch

    def _query(self, endpoint: str, params: dict = None) -> List[dict]:
        url = f"{self._base_url}/{endpoint}"
        r = requests.get(url, headers=self.__headers, params=params, auth=self._auth)

        if r.status_code != 200:
            raise RepositoryError(f"API request error: {r.text}")

        return r.json()

    def _get_all_pages(self, endpoint: str, params: dict = None, max_results: int = 0) -> List[dict]:
        """
        Gets all data (max_results = 0) or specified count for the specified endpoint
        with the specified parameters.
        @param endpoint: endpoint for receiving data
        @param params: parameters
        @param max_results: maximum number of results
        @return: list of data
        """
        data = []

        if max_results and max_results < self.__page_size:
            page_size = max_results
        else:
            page_size = self.__page_size

        if params:
            params.update({"per_page": page_size})
        else:
            params = {"per_page": page_size}

        page = 1

        while True:
            params.update({"page": page})
            data_page = self._query(endpoint, params)
            data.extend(data_page)

            if (len(data_page) < page_size) or (
                max_results and len(data) >= max_results
            ):
                break

            page += 1

        if max_results:
            return data[:max_results]
        return data

    def get_commits(self, date_from: str = None, date_to: str = None) -> List[dict]:
        """
        Gets raw info about all commits regardless of branch.
        @param date_from: start date of the period within which to look for commits
        @param date_to: end date of the period within which to look for commits
        @return: list of commits
        """
        return self._get_all_pages(
            endpoint="commits", params={"since": date_from, "until": date_to}
        )

    def get_contributors(self, count: int = 0, anon: bool = False) -> List[dict]:
        """
        Gets raw info about all contributors regardless of branch,
        sorting them by the number of contributions.

        This method can't filter commits by date. For this you must use the get_commits() method.

        When comparing data with data on the site, you must look at the contributors page,
        and not at the repository page.
        @param count: number of contributors
        @param anon: whether to include anonymous contributors in the result or not
        @return: list or contributors
        """
        return self._get_all_pages(
            endpoint="contributors", params={"anon": int(anon)}, max_results=count
        )

    def get_pull_requests(self, state=State.ALL, sort_by=Sorting.CREATE) -> List[dict]:
        """
        Gets raw information about pull requests corresponding to a specific branch and state (see the State class),
        sorting them in a specific way (see the Sorting.Prs class).
        @param state: state of pull requests ("open", "closed" or "all")
        @param sort_by: how to sort pull requests ("created", "updated", "popularity" or "long-running")
        @return: list of pull requests
        """
        return self._get_all_pages(
            endpoint="pulls",
            params={"state": state, "base": self._branch, "sort": sort_by},
        )

    def get_issues(self, state=State.ALL, sort_by=Sorting.CREATE) -> List[dict]:
        """
        Gets raw information about issues corresponding to a specific state (see the State class), sorting them
        in a specific way (see the Sorting.Issues class).
        @param state: state of issues ("open", "closed" or "all")
        @param sort_by: how to sort issues ("created", "updated" or "comments")
        @return: list of issues
        """
        return self._get_all_pages(
            endpoint="issues", params={"state": state, "sort": sort_by}
        )


class RepositoryError(Exception):
    pass
