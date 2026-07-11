from analyze_equity import main as analyze_equity
from build_features import main as build_features


def main() -> None:
    build_features()
    analyze_equity()


if __name__ == "__main__":
    main()
