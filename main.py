import subprocess

import eel
from sudoku import Sudoku


def main():
    # run tailwindcss build
    res = subprocess.call(["tailwindcss", "-i", "app/style_input.css", "-o", "app/style.css", "--minify"], shell=True)
    if res != 0:
        print("Error running tailwindcss, make sure it is installed")
        print("Did you run npm install?")
        return

    eel.init("app")
    eel.start("pages/index.html", size=(980, 700), jinja_templates="pages")


@eel.expose
def solve_sudoku(sudoku_string):
    sudoku = Sudoku(sudoku_string)
    if not sudoku.minimum_clues():
        return {'state': "minimumClues"}
    else:
        res = ""
        match sudoku.solve():
            case Sudoku.SolutionState.UniqueSolution:
                res = "unique"
            case Sudoku.SolutionState.NoSolution:
                res = "noSolution"
            case Sudoku.SolutionState.MultipleSolutions:
                res = "multipleSolutions"

        return {
            'state': res,
            'solution': sudoku.grid.tolist()
        }


if __name__ == "__main__":
    main()
