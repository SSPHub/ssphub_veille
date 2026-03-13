import argparse

from src.veille_function import extract_and_add_to_veille


def main(file: str, how: str):
    """
    Extract and add articles from tchap group to veille table on grist

    Args:
        file : path to json file
        how : choice between 'Test' and 'Veille' modalities

    """
    extract_and_add_to_veille(input_conv_file_path=file, target_table=how)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Extract articles and add them to Grist table"
    )
    parser.add_argument("-f", "--file", default="export.json")
    parser.add_argument("-t", "--table", default="Test")

    args = parser.parse_args()

    try:
        main(args.file, args.table)
    except Exception as e:
        print(f"Fatal error in pipeline: {e}")
        raise
