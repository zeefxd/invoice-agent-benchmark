import argparse
from src.interfaces.cli_runner import BenchmarkRunner

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uruchomienie Benchmarku Invoice Agenta")
    parser.add_argument("--debug", action="store_true", help="Włącza podgląd na żywo z myślenia agenta i narzędzi")
    args = parser.parse_args()

    BenchmarkRunner.execute_all(debug=args.debug)