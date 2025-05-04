import eel
from sudoku import Sudoku


def main():
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
