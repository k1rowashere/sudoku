import numpy as np
from typing import List, Tuple


class Sudoku:
    def __init__(self, initial_grid: List[List[int]] | np.ndarray = None):
        if isinstance(initial_grid, np.ndarray):
            self.initial_grid = initial_grid.copy()
        self.initial_grid = np.array(initial_grid, np.uint8) if initial_grid is not None else None
        self.grid = np.zeros((9, 9), np.uint8) if initial_grid is None else self.initial_grid.copy()

    def __str__(self):
        string = "╭───────┬───────┬───────╮\n"
        for i in range(9):
            if i % 3 == 0 and i != 0:
                string += "├───────┼───────┼───────┤\n"
            string += '│ '
            for j in range(9):
                string += str(self.grid[i, j]) if self.grid[i, j] != 0 else ' '
                string += ' '
                if j % 3 == 2 and j != 8:
                    string += '│ '
            string += '│\n'
        string += "╰───────┴───────┴───────╯"
        return string

    def color_str(self):
        # color the initial grid with red
        string = "╭───────┬───────┬───────╮\n"
        for i in range(9):
            if i % 3 == 0 and i != 0:
                string += "├───────┼───────┼───────┤\n"
            string += '│ '
            for j in range(9):
                if self.initial_grid[i, j] != 0:
                    string += f"\033[1;31m{self.grid[i, j]}\033[0m"
                else:
                    string += str(self.grid[i, j]) if self.grid[i, j] != 0 else ' '
                string += ' '
                if j % 3 == 2 and j != 8:
                    string += '│ '
            string += '│\n'

        string += "╰───────┴───────┴───────╯"
        return string

    def is_valid(self, i, j, num):
        if num in self.grid[i]:
            return False
        if num in self.grid[:, j]:
            return False
        box_row, box_col = i // 3, j // 3
        if num in self.grid[box_row * 3:box_row * 3 + 3, box_col * 3:box_col * 3 + 3]:
            return False
        return True

    def check(self):
        for i in range(9):
            for j in range(9):
                if self.grid[i, j] == 0:
                    continue
                # remove the number from the grid
                num = self.grid[i, j]
                self.grid[i, j] = 0
                is_valid = self.is_valid(i, j, num)
                self.grid[i, j] = num
                if not is_valid:
                    return False
        return True

    def solve(self):
        if self.check():
            return self._do_solve()
        else:
            return False

    def has_solution(self):
        test_game = Sudoku(self.grid)
        return test_game.solve()

    def _do_solve(self):
        for i in range(9):
            for j in range(9):
                if self.grid[i, j] != 0:
                    continue
                for num in range(1, 10):
                    if not self.is_valid(i, j, num):
                        continue

                    self.grid[i, j] = num
                    if self._do_solve():
                        return True
                    self.grid[i, j] = 0
                return False
        return True


def ac3(sudoku):
    """
    AC-3 algorithm for solving Sudoku
    https://en.wikipedia.org/wiki/AC-3_algorithm


    :param sudoku:
    :return:
    """

    X = [(i, j) for i in range(9) for j in range(9)]

    domains = np.array([[set()] * 9 for _ in range(9)], dtype=object)
    for x in X:
        if sudoku.grid[x] != 0:
            domains[x] = {int(sudoku.grid[x])}
        else:
            domains[x] = {i for i in range(1, 10)}

    def r2(x: Tuple[int, int], y: Tuple[int, int]):
        return (x[0] != y[0] or x[1] != y[1]) and (
                (x[0] == y[0]) or  # same row
                (x[1] == y[1]) or  # same column
                (x[0] // 3 == y[0] // 3 and x[1] // 3 == y[1] // 3)  # same box
        )

    def arc_reduce(x, y):
        """
        Arc reduce the domain of x with respect to y

        :param x: variable x
        :param y: variable y
        :return:
        """

        change = False
        to_remove = []

        for vx in domains[x]:
            if not any(vx != vy for vy in domains[y]):  # TODO: add a generic constraint check
                to_remove.append(vx)
                change = True

        for vx in to_remove:
            domains[x].remove(vx)

        return change

    worklist = [(x, y) for x in X for y in X if r2(x, y)]

    while worklist:
        x, y = worklist.pop()
        if arc_reduce(x, y):
            if not domains[x]:
                return False
            for z in X:
                if z != y and r2(z, x):
                    worklist.append((z, x))
    return domains


def main():
    sudoku = [
        [7, 9, 0, 0, 1, 3, 6, 0, 0],
        [4, 0, 0, 0, 7, 0, 3, 0, 0],
        [1, 0, 0, 2, 4, 0, 9, 7, 5],
        [5, 0, 0, 6, 0, 0, 2, 0, 7],
        [0, 7, 0, 0, 0, 1, 8, 0, 0],
        [8, 0, 6, 9, 2, 0, 5, 0, 0],
        [6, 0, 1, 0, 0, 2, 0, 5, 3],
        [3, 0, 0, 0, 0, 0, 4, 0, 9],
        [0, 2, 4, 0, 3, 5, 0, 0, 0]
    ]

    sudoku = Sudoku(sudoku)
    print(sudoku.color_str())

    print(ac3(sudoku))

    sudoku.solve()
    print(sudoku.color_str())


if __name__ == '__main__':
    main()
