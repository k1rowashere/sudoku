import time
from enum import Enum
import numpy as np
import random

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


def fn(x):
    count = x.bit_count()
    return count if count != 1 else 10


COUNT_BITS_VECT = np.vectorize(fn)

ENABLE_LOGGING = True


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
            self.initial_grid = np.zeros((9, 9), dtype=np.uint16)

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

    def forward_checking(self, cell: tuple[int, int], assignedValue: int) -> bool:
        """
        Performs forward checking after assigning a value to a cell.
        Returns False if any neighbor's domain becomes empty.
        """
        valueBit = 1 << (assignedValue - 1)
        neighbors = NEIGHBORS[cell[0] * 9 + cell[1]]

        for neighbor in neighbors:
            # skip assigned cells
            if self.grid[neighbor].bit_count() == 1:
                continue

            # neighbor's domain contains the assigned value
            if self.grid[neighbor] & valueBit:
                # remove the value from neighbor's domain
                self.grid[neighbor] &= ~valueBit

                #  domain empty, return failure
                if self.grid[neighbor] == 0:
                    return False

        return True

    def prune_domains(self):
    # Remove impossible values from empty cells based on row/column/box constraints."""
       
        for i, j in np.ndindex(9, 9):
            if self.grid[i, j].bit_count() != 1:  # Only prune empty/multi-value cells
                # Collect forbidden values from row/column/box
                print("here ")
                forbidden = 0
                for x in range(9):
                    forbidden |= self.grid[i, x]  # Row constraints
                    forbidden |= self.grid[x, j]  # Column constraints
                
                # Box constraints
                box_i, box_j = (i // 3) * 3, (j // 3) * 3
                for x, y in np.ndindex(3, 3):
                    forbidden |= self.grid[box_i + x, box_j + y]
                
                # Remove forbidden values (keep only possible ones)
                self.grid[i, j] &= ~forbidden
                
                # Early exit if any cell becomes empty
                if self.grid[i, j] == 0:
                    return False
        return True

    def solve(self, changed_cell: tuple[int, int] = None) -> SolutionState:
        # if not self.prune_domains():
        #     return self.SolutionState.NoSolution
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

        # Score values by how few they constrain neighbors (LCV heuristic)
        def lcv_score(val):
            score = 0
            valueBit = 1 << (val - 1)  # Convert value (1-9) to bit position (0-8)
            for neighbor in NEIGHBORS[cell[0] * 9 + cell[1]]:
                if self.grid[neighbor] & valueBit:
                    score += 1
            return score

        domain = [k + 1 for k in range(9) if self.grid[cell] & (1 << k)]
        sorted_values = sorted(domain, key=lcv_score)

        if ENABLE_LOGGING:
            print(f'{self:color}')
            print("LCV:")
            print(f"    Cell {cell} possible values: {domain}")
            print(f"    LCV scores: {[(v, lcv_score(v)) for v in domain]}")
            print(f"    LCV Sorted values: {sorted_values}")
            print('-' * 20)

        solutions = []

        child_state = None
        for num in sorted_values:
            new_grid = self.grid.copy()
            new_grid[cell] = 1 << (num - 1)

            new_sudoku = Sudoku(self.initial_grid, new_grid)

            new_state = new_sudoku.solve(cell)

            if new_state != Sudoku.SolutionState.NoSolution:
                child_state = new_state
                solutions.append(new_sudoku.grid)

        match len(solutions):
            case 0:
                return Sudoku.SolutionState.NoSolution
            case 1:
                self.grid = solutions[0]
                return child_state
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
    def ac3_optimized(domains: np.ndarray[(9, 9), np.uint16], worklist=WORKLIST) -> bool:
        if ENABLE_LOGGING:
            print("BEGIN: AC3")

        worklist = list(worklist)

        while worklist:
            x, y = worklist.pop()
            y_val = domains[y]

            #  y is a singleton and x's domain contains y's value
            if (y_val & (y_val - 1)) == 0 and (domains[x] & y_val):
                if ENABLE_LOGGING:
                    bit_to_num = {1 << i: i + 1 for i in range(9)}
                    removed_value = bit_to_num[y_val]
                    x_domain_before = [k + 1 for k in range(9) if domains[x] & (1 << k)]
                    # x_domain_after = [bit_to_num[1 << k] for k in range(9) if domains[x] & (1 << k)]
                    x_domain_after = [x for x in x_domain_before if domains[y] & (1 << x-1) ==0]
                    print(f"Revising arc ({x}, {y})")
                    print(f"Current domain of {x}: {x_domain_before}")
                    print(f"Domain of {y}: [{removed_value}]")
                    print(f"Removed value {removed_value} from {x} because no supporting value exists in{y}")
                    print(f"Updated domain of {x}: {x_domain_after}\n\n")

                # Remove y's value from x's domain
                domains[x] &= ~y_val

                if not domains[x]:
                    return False

                for neighbor in NEIGHBORS[x[0] * 9 + x[1]]:
                    if neighbor != y:
                        worklist.append((neighbor, x))

        return True

    def generate_k_empty(self, k):
        def fill_diagonal():
            # fill diagonal boxes
            for k in range(0, 9, 3):
                filled = 0
                for i in range(3):
                    for j in range(3):
                        while True:
                            num = random.randint(1, 9)
                            num_bit = 1 << (num - 1)
                            if not (filled & num_bit):
                                break
                        self.grid[k + i, k + j] = num_bit
                        filled |= num_bit

        def fill_remaining(i=0, j=0):
            # recursively fill remaining cells
            if i == 9:
                return True
            if j == 9:
                return fill_remaining(i + 1, 0)
            cell = (i, j)
            if self.grid[cell].bit_count() == 1:
                return fill_remaining(i, j + 1)

            # get possible values
            filled = 0
            # check row and column
            for x in range(9):
                if self.grid[i, x].bit_count() == 1:
                    filled |= self.grid[i, x]

                if self.grid[x, j].bit_count() == 1:
                    filled |= self.grid[x, j]
            # check square
            square_i, square_j = i // 3 * 3, j // 3 * 3
            for x in range(3):
                for y in range(3):
                    if self.grid[square_i + x, square_j + y].bit_count() == 1:
                        filled |= self.grid[square_i + x, square_j + y]

            # try all possible numbers
            for num in range(1, 10):
                num_bit = 1 << (num - 1)
                if not (filled & num_bit):
                    self.grid[i, j] = num_bit
                    if fill_remaining(i, j + 1):
                        return True
                    self.grid[i, j] = 511
            return False

        def remove_k_digits(k):
            # remove K digits and solvable
            count = 0
            cells = [(i, j) for i in range(9) for j in range(9)]
            random.shuffle(cells)

            for i, j in cells:
                if count >= k:
                    break
                backup = self.grid[i, j]
                self.grid[i, j] = 511  # removing

                # Check if still solvable
                temp = Sudoku(self.initial_grid, self.grid.copy())

                if temp.solve() == self.SolutionState.UniqueSolution:
                    count += 1
                else:
                    self.grid[i, j] = backup  # Restore if removal breaks solv-ability
            return self

        """Generate a Sudoku with exactly k empty cells."""
        while True:
            fill_diagonal()
            fill_remaining()
            if self.solve() == self.SolutionState.UniqueSolution:
                remove_k_digits(k)

                # copy to initial grid
                self.initial_grid = np.array(
                    [
                        [int(x).bit_length() if x.bit_count() == 1 else 0 for x in row]
                        for row in self.grid
                    ]
                )
                # cleanup grid
                for i in range(9):
                    for j in range(9):
                        if self.initial_grid[i, j] == 0:
                            self.initial_grid[i, j] = 511

                return self


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
    # sudoku = Sudoku("..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9")
    # sudoku = Sudoku(".8.6543212461739853519287461285376946348921577954618325192864734723195688637452.9")
    # Not enough unique values:
    # sudoku = Sudoku(".....5.8....6.1.43..........1.5........1.6...3.......553.....61........4.........")
    # sudoku = Sudoku("9..8...........5............2..1...3.1.....6....4...7.7.86.........3.1..4.....2..")
    # intermediate
    # sudoku = Sudoku(".2.6.8...58...97......4....37....5..6.......4..8....13....2......98...36...3.6.9.")
    # easy -- > unique
    sudoku = Sudoku("...26.7.168..7..9.19...45..82.1...4...46.29...5...3.28..93...74.4..5..367.3.18...")

    # sudoku = Sudoku().generate_k_empty(30)

    print(f"{sudoku:color}")
    print(sudoku.to_string())
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
