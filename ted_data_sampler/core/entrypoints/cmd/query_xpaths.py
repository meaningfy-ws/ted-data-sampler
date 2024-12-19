import argparse
from logging import Logger
from pathlib import Path

from future.moves import sys

from ted_data_sampler.core.services.logger import setup_logger
from ted_data_sampler.core.services.xpath_query_service import query_notices_with_given_xpaths


class QueryXPathsException(Exception):
    """"""


def main():
    parser = argparse.ArgumentParser(
        description="Query given list of XPaths in the list of XML files stores the result in tabular format in output file")
    parser.add_argument("-o", "--output_file", required=True, help="Path to the output file.")
    parser.add_argument("-i", "--notices_file_list", required=True, help="Path to file with list of all notices")
    parser.add_argument("-x", "--xpaths_file", required=True, help="File with list of xpaths to be queried")

    args = parser.parse_args()
    output_file_path = Path(args.output_file)
    notices_file_path = Path(args.notices_file_list)
    xpaths_file = Path(args.xpaths_file)

    if not output_file_path.is_file():
        raise QueryXPathsException(f"File {output_file_path} does not exist")

    if not notices_file_path.is_file():
        raise QueryXPathsException(f"File {notices_file_path} does not exist")

    if not xpaths_file.is_file():
        raise QueryXPathsException(f"File {xpaths_file} does not exist")

    logger: Logger = setup_logger([sys.stdout])

    try:
        result = query_notices_with_given_xpaths(xpaths=xpaths_file.read_text().splitlines(),
                                                 notice_paths=[Path(notice_path_str) for notice_path_str in notices_file_path.read_text().splitlines()],
                                                 logger=logger)
        output_file_path.write_text(str(result))
    except Exception as e:
        logger.error(e)
        raise QueryXPathsException(e)


if __name__ == "__main__":
    main()
