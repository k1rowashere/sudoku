import time
from enum import Enum
import numpy as np
import random
from copy import deepcopy

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

    class SolutionState(Enum):
        NoSolution = 0
        UniqueSolution = 1
        MultipleSolutions = 2,
    
    def forward_checking(self, cell: tuple[int, int], assignedValue: int) -> bool:
        """
        Performs forward checking after assigning a value to a cell.
        Returns False if any neighbor's domain becomes empty.
        """
        # print("forwarddd")
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


    def solve(self, changed_cell: tuple[int, int] = None) -> SolutionState:
        # use ac3 to reduce the search space
        # print(self)
        if changed_cell is not None:
            res = self.ac3_optimized(self.grid, WORKLISTS[changed_cell[0] * 9 + changed_cell[1]])
        else:
            res = self.ac3_optimized(self.grid)
        if res is False:
            return Sudoku.SolutionState.NoSolution
        print(self)

        # Find the cell with the fewest possibilities (MRV heuristic)
        cell = np.argmin(COUNT_BITS_VECT(self.grid))
        cell = (cell // 9, cell % 9)

        if self.grid[cell].bit_count() == 1:
            # All cells have exactly one value
            return Sudoku.SolutionState.UniqueSolution

         # Get possible values for the cell (1-9)
        possible_values = [k + 1 for k in range(9) if self.grid[cell] & (1 << k)]
      
        # Score values by how few they constrain neighbors (LCV)
        def lcv_score(val):
            score = 0
            valueBit = 1 << (val - 1)  # Convert value (1-9) to bit position (0-8)
            for neighbor in NEIGHBORS[cell[0] * 9 + cell[1]]:
                if self.grid[neighbor] & valueBit:
                    score += 1
            return score

        # Sort values by LCV
        sorted_values = sorted(possible_values, key=lcv_score)
        # print(f"Cell {cell} possible values: {possible_values}")
        # print(f"LCV scores: {[(v, lcv_score(v)) for v in possible_values]}")
        # print(f"LCV Sorted values: {sorted_values}")

        solutions = []

        # Try each possibility
        #for num in [k + 1 for k in range(9) if self.grid[cell] & (1 << k)]:
        for num in sorted_values:
            new_grid = self.grid.copy()
            new_grid[cell] = 1 << (num - 1)
            
            new_sudoku = Sudoku(self.initial_grid, new_grid)
            # if not new_sudoku.forward_checking(cell, num):
            #     continue  # Skip if forward checking fails

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
        bit_to_num = {1 << i: i+1 for i in range(9)}
       
        while worklist:
            x, y = worklist.pop()
            y_val = domains[y]
            
            #  y is a singleton and x's domain contains y's value
            if (y_val & (y_val - 1)) == 0 and (domains[x] & y_val):
                removed_value = bit_to_num[y_val]
                x_domain_before = [bit_to_num[1 << k] for k in range(9) if domains[x] & (1 << k)]
                print(f"Revising arc ({x}, {y})")
                print(f"Current domain of {x}: {x_domain_before}")
                print(f"Domain of {y}: [{removed_value}]")

                # Remove y's value from x's domain
                domains[x] &= ~y_val
                
                x_domain_after = [bit_to_num[1 << k] for k in range(9) if domains[x] & (1 << k)]
                
                print(f"Removed value {removed_value} from {x} because no supporting value exists in {y}")
                print(f"Updated domain of {x}: {x_domain_after}\n\n")

                if not domains[x]:
                    return False
            
                for neighbor in NEIGHBORS[x[0] * 9 + x[1]]:
                    if neighbor != y:
                        worklist.append((neighbor, x))

        return True
    

    def fillSquare(self, row, col):
        # fill a 3x3 box with random valid numbers
        filled = 0
        for i in range(3):
            for j in range(3):
                while True:
                    num = random.randint(1, 9)
                    num_bit = 1 << (num - 1)
                    if not (filled & num_bit):
                        break
                self.grid[row + i, col + j] = num_bit
                filled |= num_bit
        print(self)

    def fillDiagonal(self):
        # fill diagonal boxes
        for i in range(0, 9, 3):
            self.fillSquare(i, i)

    def fill_remaining(self, i=0, j=0):
        # recursively fill remaining cells 
        if i == 9:
            return True
        if j == 9:
            return self.fill_remaining(i + 1, 0)
        cell = (i, j)
        # print(cell)
        if self.grid[cell].bit_count() == 1:
            return self.fill_remaining(i, j + 1) 

        # get possible values 
        filled = 0
        # check row and column
        for x in range(9):
            if self.grid[i, x].bit_count() == 1:
                # print("row", (i, x))
                filled |= self.grid[i, x]
            
            if self.grid[x, j].bit_count() == 1:
                # print("col", (x, j))
                filled |= self.grid[x, j]
        # check square
        square_i, square_j = i // 3* 3, j // 3 * 3
        for x in range(3):
            for y in range(3):
                if self.grid[square_i + x, square_j + y].bit_count() == 1:
                    # print("diag", (box_i + x, box_j + y))
                    filled |= self.grid[square_i + x, square_j + y]
      
        # try all possible numbers
        for num in range(1, 10):
            num_bit = 1 << (num - 1)
            if not (filled & num_bit):
                # print("set me")
                self.grid[i, j] = num_bit
                if self.fill_remaining(i, j + 1) :
                    return True
                self.grid[i, j] = 511
        return False

    def remove_k_digits(self, k):
        # remove K digits and solvable
        count = 0
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        print("remove")
        # print(cells)

        for i, j in cells:
            if count >= k:
                break
            backup = self.grid[i, j]
            self.grid[i, j] = 511  # removing
        
            # Check if still solvable
            temp = Sudoku(self.initial_grid,self.grid.copy())
           
            if temp.solve() == self.SolutionState.UniqueSolution:
                count += 1
            else:
                self.grid[i, j] = backup  # Restore if removal breaks solvability
        return self

    
    def generateKEmpty(self, k):
        """Generate a Sudoku with exactly k empty cells."""
        while True:
            # empty_grid = np.zeros((9, 9), dtype=np.uint16)
            # sudoku = Sudoku(empty_grid)
    
            # 1. Fill diagonal boxes
            self.fillDiagonal()
            print("fill diagonal")
            if not self.fill_remaining():
                print("fill remain")     
            print("Complete Puzzle")    
            print(self)
            if self.solve() == self.SolutionState.UniqueSolution:
                self.remove_k_digits(k)
                return self
   
def main():
    # given in assignment pdf:
    # sudoku = Sudoku([
    #     [7, 9, 5, 0, 1, 3, 6, 0, 0],
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
    # sudoku = Sudoku("4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......") # ---> 6.8s ---> unique
    # https://en.wikipedia.org/wiki/File:Sudoku_puzzle_hard_for_brute_force.svg
    # sudoku = Sudoku("..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9") # --->
   # sudoku = Sudoku(".8.6543212461739853519287461285376946348921577954618325192864734723195688637452.9")
    # Not enough unique values:
    # sudoku = Sudoku(".....5.8....6.1.43..........1.5........1.6...3.......553.....61........4.........")
    # sudoku = Sudoku("9..8...........5............2..1...3.1.....6....4...7.7.86.........3.1..4.....2..")
     #intermediate
    # sudoku = Sudoku(".2.6.8...58...97......4....37....5..6.......4..8....13....2......98...36...3.6.9.")
    #easy -- > unique
    sudoku = Sudoku("...26.7.168..7..9.19...45..82.1...4...46.29...5...3.28..93...74.4..5..367.3.18...")

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
    # main()
    empty_grid = np.zeros((9, 9), dtype=np.uint16)
    sudoku = Sudoku(empty_grid)
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
    
    sudoku = sudoku.generateKEmpty(k = 30)
    # if not new_puzzle.minimum_clues():
    #     print("Not enough clues (>= 17, > 7 distinct digits)")
    # else :
    print(f"{sudoku:color}")
    # start = time.time()
    # match sudoku.solve():
    #         case Sudoku.SolutionState.NoSolution:
    #             print("No solution")
    #         case Sudoku.SolutionState.UniqueSolution:
    #             print("Unique solution")
    #             print(f"{sudoku:color}")
    #         case Sudoku.SolutionState.MultipleSolutions:
    #             print("Multiple solutions")
    #             print(f'{sudoku:color}')

    # print(f"Solution found in {time.time() - start:.2f}s")