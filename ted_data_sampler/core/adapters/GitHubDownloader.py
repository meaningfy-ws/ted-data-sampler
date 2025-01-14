import pathlib
import shutil
import subprocess
import tempfile
from typing import List


class GitHubDownloaderException(Exception):
    """

    """


class GitHubDownloader:

    def __init__(self, github_repository_url: str, branch_or_tag_name: str) -> None:
        """
        Option can be branch or tag name, not both
        :param github_repository_url:
        :param branch_or_tag_name:
        :param repository_name:
        """
        self.github_repository_url = github_repository_url
        self.branch_or_tag_name = branch_or_tag_name

    def download(self, result_dir_path: pathlib.Path, download_resources_filter: List[str] = None) -> None:
        """
            This method downloads a GitHub repository and save it at the result_dir_path provided.
            If download_resources_filter is provided, only the resources with the names in the list will be downloaded.
        :param result_dir_path:
        :param download_resources_filter:
        :return:
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir_path = pathlib.Path(tmp_dir)
            bash_script = f"cd {temp_dir_path} && git clone --depth=1 --single-branch --branch {self.branch_or_tag_name} {self.github_repository_url}"
            subprocess.run(bash_script, shell=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT)
            dir_contents = list(temp_dir_path.iterdir())

            if len(dir_contents) != 1:
                raise GitHubDownloaderException("Error fetching repository, check tag name")

            repository_name = dir_contents[0].name

            repository_content_dir_path = temp_dir_path / repository_name
            if download_resources_filter:
                for content_path in repository_content_dir_path.iterdir():
                    if content_path.name in download_resources_filter:
                        if content_path.is_dir():
                            shutil.copytree(content_path, result_dir_path / content_path.name, dirs_exist_ok=True)
                        elif content_path.is_file():
                            shutil.copyfile(content_path, result_dir_path / content_path.name)
            else:
                shutil.copytree(temp_dir_path, repository_content_dir_path, dirs_exist_ok=True)
