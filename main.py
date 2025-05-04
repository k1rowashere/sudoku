import eel


def main():
    eel.init("app")
    eel.start("pages/index.html", size=(980, 700), jinja_templates="pages")


@eel.expose
def solve_sudoku(sudoku_string):
    from sudoku import Sudoku

    sudoku = Sudoku(sudoku_string)
    res = sudoku.solve()
    return sudoku.to_string()

    # if sudoku.is_solved():
    #     return sudoku.to_string()
    # else:
    #     return "No solution"


if __name__ == "__main__":
    main()
