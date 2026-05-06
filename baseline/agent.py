import typer

from src.interfaces.cli_runner import BenchmarkRunner


app = typer.Typer(help="Uruchomienie benchmarku baseline invoice agenta.")


@app.command()
def run(
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Włącza podgląd na żywo z myślenia agenta i narzędzi.",
    )
):
    BenchmarkRunner.execute_all(debug=debug)


if __name__ == "__main__":
    app()
