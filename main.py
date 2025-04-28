import numpy as np
from typing import List, Tuple


class Sudoku:
    def __init__(self, initial_grid: List[List[int]] | np.ndarray = None, domains: np.ndarray = None):
        self.initial_grid = (
            initial_grid if isinstance(initial_grid, np.ndarray) else
            np.array(initial_grid, np.uint8) if isinstance(initial_grid, list) else
            None
        )
        self.grid: np.ndarray[set[int]]
        if domains is not None:
            self.grid = domains
        else:
            self.grid = np.ndarray((9, 9), dtype=set)
            for x in [(i, j) for i in range(9) for j in range(9)]:
                if self.initial_grid[x] != 0:
                    self.grid[x] = {int(self.initial_grid[x])}
                else:
                    self.grid[x] = {i for i in range(1, 10)}

    def __str__(self):
        return self.__format__(self)

    def __format__(self, format_spec):
        string = "╭───────┬───────┬───────╮\n"
        for i in range(9):
            if i % 3 == 0 and i != 0:
                string += "├───────┼───────┼───────┤\n"
            string += '│ '
            for j in range(9):
                if self.initial_grid[i, j] != 0:
                    if format_spec == 'color':
                        string += f"\033[1;31m{self.initial_grid[i, j]}\033[0m"
                    else:
                        string += str(self.initial_grid[i, j])
                elif len(self.grid[i, j]) == 1:
                    string += str(list(self.grid[i, j])[0])
                else:
                    string += '_'
                string += ' '
                if j % 3 == 2 and j != 8:
                    string += '│ '
            string += '│\n'

        string += "╰───────┴───────┴───────╯"
        return string

    def solve(self) -> bool:
        if self.ac3(self.grid) is False:
            return False

        # TODO:
        #  - heuristics (MRV, LCV)
        #  - handle multiple solutions
        for i in range(9):
            for j in range(9):
                cell = (i, j)
                if len(self.grid[cell]) == 1:
                    continue
                if len(self.grid[cell]) == 0:
                    return False

                to_remove = set()

                # if the cell has more than one possibility, try each one
                # use ac3 to reduce the search space
                for num in self.grid[cell]:
                    new_grid = self.grid.copy()
                    new_grid[cell] = {num}

                    new_sudoku = Sudoku(self.initial_grid, new_grid)

                    if new_sudoku.solve() is False:
                        to_remove.add(num)
                    else:
                        self.grid = new_sudoku.grid
                        return True

                self.grid[cell] -= to_remove
        return True

    @staticmethod
    def ac3(domains: np.ndarray[set[int]]) -> bool:
        """
        AC-3 algorithm for arc consistency
        https://en.wikipedia.org/wiki/AC-3_algorithm

        :param domains: Domains of the variables
        :return: True if the domains are arc consistent, False otherwise
        """

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
            to_remove = set()

            for vx in domains[x]:
                if not any(vx != vy for vy in domains[y]):  # TODO: add a generic constraint check
                    to_remove.add(vx)
                    change = True

            domains[x] -= to_remove

            return change

        X = [(i, j) for i in range(9) for j in range(9)]
        worklist = [(x, y) for x in X for y in X if r2(x, y)]

        while worklist:
            x, y = worklist.pop()
            if arc_reduce(x, y):
                if not domains[x]:
                    return False
                for z in X:
                    if z != y and r2(z, x):
                        worklist.append((z, x))
        return True


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
    if sudoku.solve():
        print(f'{sudoku:color}')
    else:
        print("No solution found.")


if __name__ == '__main__':
    main()
