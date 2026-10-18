


import argparse
from html import parser

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("Number")
    parser.add_argument("word")

    args = parser.parse_args()

    print(f"Number: {args.Number}")
    print(f"Word: {args.word}")

    print("Hello, World!")


if __name__ == "__main__":
    main()
