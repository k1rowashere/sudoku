import time
from enum import Enum
import numpy as np

# precompute worklist and neighbors for faster execution
WORKLISTS = tuple([[
    *[((i, k), (i, j)) for k in range(9) if k != j],  # Row
    *[((k, j), (i, j)) for k in range(9) if k != i],  # Column
    *[((i // 3 * 3 + di, j // 3 * 3 + dj), (i, j))
      for di in range(3) for dj in range(3)
      if di != i % 3 and dj != j % 3]  # Box (w/o same row/column)
] for i in range(9) for j in range(9)])
NEIGHBORS = tuple([[x[0] for x in xs] for xs in WORKLISTS])
WORKLIST = tuple([x for xs in WORKLISTS for x in xs])

COUNT_BITS_VECT = np.vectorize(lambda x: x.bit_count() if x.bit_count() != 1 else 10)


class Sudoku:
    initial_grid: np.ndarray[(9, 9), np.dtype[np.uint16]]
    grid: np.ndarray[(9, 9), np.uint16]

    def __init__(self, initial_grid=None, grid=None):
        """
        :type initial_grid: str | list[list[int]] | np.ndarray[tuple[int, int], np.dtype[np.uint16]] | None
        :type grid: np.ndarray[(9, 9), np.uint16] | None
        """
        if isinstance(initial_grid, np.ndarray):
            self.initial_grid = initial_grid
        elif isinstance(initial_grid, str):
            self.initial_grid = self.from_string(initial_grid)
        elif isinstance(initial_grid, list):
            self.initial_grid = np.array(initial_grid, np.uint16)
        else:
            np.zeros((9, 9), dtype=np.uint16)

        if grid is not None:
            self.grid = grid
        else:
            self.grid = np.ndarray((9, 9), dtype=np.uint16)
            for x in [(i, j) for i in range(9) for j in range(9)]:
                if self.initial_grid[x] != 0:
                    self.grid[x] = 1 << (self.initial_grid[x] - 1)
                else:
                    self.grid[x] = 0b1_1111_1111

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
                elif self.grid[i, j].bit_count() == 1:
                    string += str(int(self.grid[i, j]).bit_length())
                else:
                    string += '_'
                string += ' '
                if j % 3 == 2 and j != 8:
                    string += '│ '
            string += '│\n'

        string += "╰───────┴───────┴───────╯"
        return string

    @staticmethod
    def from_string(string: str):
        board = np.ndarray((9, 9), dtype=np.uint16)
        for i, ch in enumerate(string):
            if ch == ' ':
                continue
            if ch == '.':
                board.flat[i] = 0
            else:
                board.flat[i] = int(ch)
        return board

    def to_string(self):
        string = ""
        for i in range(9):
            for j in range(9):
                if self.grid[i, j].bit_count() == 1:
                    string += str(int(self.grid[i, j]).bit_length())
                else:
                    string += '.'
        return string

    def is_solved(self):
        for i in range(9):
            for j in range(9):
                if self.grid[i, j].bit_count() != 1:
                    return False
        return self.ac3_optimized(self.grid)

    class SolutionState(Enum):
        NoSolution = 0
        UniqueSolution = 1
        MultipleSolutions = 2,

    def solve(self, changed_cell: tuple[int, int] = None) -> SolutionState:
        # use ac3 to reduce the search space
        if changed_cell is not None:
            res = self.ac3_optimized(self.grid, WORKLISTS[changed_cell[0] * 9 + changed_cell[1]])
        else:
            res = self.ac3_optimized(self.grid)

        if res is False:
            return Sudoku.SolutionState.NoSolution

        # Find the cell with the fewest possibilities (MRV heuristic)
        cell = np.argmin(COUNT_BITS_VECT(self.grid))
        cell = (cell // 9, cell % 9)

        if self.grid[cell].bit_count() == 1:
            # All cells have exactly one value
            return Sudoku.SolutionState.UniqueSolution

        solutions = []

        # Try each possibility
        for num in [k + 1 for k in range(9) if self.grid[cell] & (1 << k)]:
            new_grid = self.grid.copy()
            new_grid[cell] = 1 << (num - 1)
            new_sudoku = Sudoku(self.initial_grid, new_grid)
            if new_sudoku.solve(cell) != Sudoku.SolutionState.NoSolution:
                solutions.append(new_sudoku.grid)

        match len(solutions):
            case 0:
                return Sudoku.SolutionState.NoSolution
            case 1:
                self.grid = solutions[0]
                return Sudoku.SolutionState.UniqueSolution
            case _:
                # merge the solutions
                for x in [(i, j) for i in range(9) for j in range(9)]:
                    self.grid[x] = 0
                    for solution in solutions:
                        self.grid[x] |= solution[x]
                return Sudoku.SolutionState.MultipleSolutions

    def minimum_clues(self):
        """
        Checks for early termination conditions:
            - Must have >= 17 clues
            - Must have 8, 9 distinct digits
        :return: True if the puzzle satisfies the conditions
        """
        if len(np.unique(self.initial_grid[self.initial_grid != 0])) < 8:
            return False
        if np.count_nonzero(self.initial_grid) < 17:
            return False
        return True

    @staticmethod
    def ac3(domains: np.ndarray[(9, 9), np.uint16]) -> bool:
        """
        AC-3 algorithm for arc consistency
        https://en.wikipedia.org/wiki/AC-3_algorithm

        :param domains: Domains of the variables
        :return: True if the domains are arc consistent, False otherwise
        """

        def arc_reduce(x, y):
            """
            Arc reduce the domain of x with respect to y
            Adapted for Sudoku using bit operations

            :param x: variable x
            :param y: variable y
            :return: True if domain of x changed
            """
            if domains[y].bit_count() == 1 and domains[x] & domains[y]:
                domains[x] &= ~(domains[y])
                return True

            return False

        def r2(x: tuple[int, int], y: tuple[int, int]):
            return (x != y) and (
                    (x[0] == y[0]) or  # same row
                    (x[1] == y[1]) or  # same column
                    (x[0] // 3 == y[0] // 3 and x[1] // 3 == y[1] // 3)  # same box
            )

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

    @staticmethod
    def ac3_optimized(domains: np.ndarray[(9, 9), np.uint16], worklist=WORKLIST) -> bool:
        worklist = list(worklist)

        while worklist:
            x, y = worklist.pop()
            y_val = domains[y]
            if (y_val & (y_val - 1)) == 0 and domains[x] & y_val:
                domains[x] &= ~y_val

                if not domains[x]:
                    return False

                for neighbor in NEIGHBORS[x[0] * 9 + x[1]]:
                    if neighbor != y:
                        worklist.append((neighbor, x))

        return True


def main():
    # given in assignment pdf:
    # sudoku = Sudoku([
    #     [7, 9, 0, 0, 1, 3, 6, 0, 0],
    #     [4, 0, 0, 0, 7, 0, 3, 0, 0],
    #     [1, 0, 0, 2, 4, 0, 9, 7, 5],
    #     [5, 0, 0, 6, 0, 0, 2, 0, 7],
    #     [0, 7, 0, 0, 0, 1, 8, 0, 0],
    #     [8, 0, 6, 9, 2, 0, 5, 0, 0],
    #     [6, 0, 1, 0, 0, 2, 0, 5, 3],
    #     [3, 0, 0, 0, 0, 0, 4, 0, 9],
    #     [0, 2, 4, 0, 3, 5, 0, 0, 0]
    # ])

    # slow cases:
    # sudoku = Sudoku("4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......")
    # https://en.wikipedia.org/wiki/File:Sudoku_puzzle_hard_for_brute_force.svg
    sudoku = Sudoku("..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9")
    # Not enough unique values:
    # sudoku = Sudoku(".....5.8....6.1.43..........1.5........1.6...3.......553.....61........4.........")
    # sudoku = Sudoku("9..8...........5............2..1...3.1.....6....4...7.7.86.........3.1..4.....2..")

    print(f"{sudoku:color}")
    print("-" * 25)
    start = time.time()

    if not sudoku.minimum_clues():
        print("Not enough clues (>= 17, > 7 distinct digits)")
    else:
        match sudoku.solve():
            case Sudoku.SolutionState.NoSolution:
                print("No solution")
            case Sudoku.SolutionState.UniqueSolution:
                print("Unique solution")
                print(f"{sudoku:color}")
            case Sudoku.SolutionState.MultipleSolutions:
                print("Multiple solutions")
                print(f'{sudoku:color}')

    print(f"Solution found in {time.time() - start:.2f}s")


if __name__ == '__main__':
    main()
