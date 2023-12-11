import copy 
from itertools import permutations
from operator import itemgetter
import timeit


WHITE = 0
CLUE = -1
BLACK = -2
DOWN = 'down'
RIGHT = 'right'
DIGITS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

class Cell():
    def __init__(self, location, category):
        self.location = location
        self.category = category

class Clue():
    def __init__(self, direction, length, goal):
        self.direction = direction
        self.goal = goal
        self.location = None
        self.length = length

class ClueCell(Cell):
    def __init__(self, location, down_clue, right_clue):
        super().__init__(location, category = CLUE)
        self.down_clue = down_clue
        self.right_clue = right_clue
        if down_clue is not None:
            self.down_clue.location = self.location
        if right_clue is not None:
            self.right_clue.location = self.location

class WhiteCell(Cell):
    def __init__(self, location, value = 0):
        super().__init__(location, category=WHITE)
        self.value = value

class BlackCell(Cell):
    def __init__(self, location):
        super().__init__(location, category=BLACK)

class KakuroBoard():
    def __init__(self, height, width, cells):
        self.height = height
        self.width = width
        self.cells = cells
        self.clues = self.get_clues()
        self.board = self.get_board()
        self.print_board()

    def get_clues(self):
        clues = []
        for c in self.cells:
            if c.category == CLUE:
                if c.down_clue is not None:
                    clues.append(c.down_clue)
                if c.right_clue is not None:
                    clues.append(c.right_clue)
        return clues
    
    def get_board(self):
        board = [[WhiteCell((i,j)) for j in range(self.width)] for i in range(self.height)]
        for c in self.cells:
            board[c.location[0]][c.location[1]] = c
        return board
    
    def print_board(self):
        for i in range(self.height):
            for j in range(self.width):
                cell = self.board[i][j]
                if cell.category == BLACK:
                    print("B", end=" ")
                elif cell.category == CLUE:
                    print("C", end=" ")
                elif cell.category == WHITE:
                    print(cell.value, end=" ")
            print()
        print()
    def get_cell(self, clue):
        cell_set = []
        if clue.direction == RIGHT:
            for i in range(clue.length):
                cell_set.append(self.board[clue.location[0]][clue.location[1] + i+1])
        elif clue.direction == DOWN:
            for i in range(clue.length):
                cell_set.append(self.board[clue.location[0] + i+1][clue.location[1]])
        return cell_set
    
    def assign_clue(self, clue, value_set):
        if clue.direction == DOWN:
            for i in range(clue.length):
                self.board[clue.location[0] + i + 1][clue.location[1]].value = value_set[i]
        elif clue.direction == RIGHT:
            for i in range(clue.length):
                self.board[clue.location[0]][clue.location[1] + i + 1].value = value_set[i]
    
    def is_clue_assigned(self, clue):
        return self.clue_unassigned_count(clue) == 0
    
    def clue_unassigned_count(self, clue):
        cell_set = self.get_cell(clue)
        unassigned_count = 0
        for c in cell_set:
            if c.value == 0:
                unassigned_count+= 1
        return unassigned_count
    
    def is_complete(self):
        is_complete = True
        for i in range(self.height):
            for j in range(self.width):
                if self.board[i][j].category == WHITE and self.board[i][j].value == 0:
                    is_complete = False
        return is_complete
    
    def is_consistent(self):
        for cl in self.clues:
            cell_set = self.get_cell(cl)
            if self.is_clue_assigned(cl):
                current_sum = 0
                values = []
                for c in cell_set:
                    values.append(c.value)
                    current_sum += c.value
                if current_sum != cl.goal or any(values.count(v) > 1 for v in values):
                    return False
        return True
    

class KakuroAgent():
    def __init__(self, board):
        self.board = board

    def select_unassigned_clue(self, assigment):
        for c in assigment.clues:
            if not assigment.is_clue_assigned(c):
                return c
    
    def order_domain_values(self, clue, cell_set, assignment):
        value_sets = []
        assigned_cells = []
        unassigned_cells = []
        allowed_values = copy.deepcopy(DIGITS)

        for cell in cell_set:
            if cell.value == 0:
                unassigned_cells.append(cell)
            else:
                if cell.value in allowed_values:
                    allowed_values.remove(cell.value)
                assigned_cells.append(cell)

        current_sum = 0
        for cell in assigned_cells:
            current_sum += cell.value

        net_goal_sum = clue.goal - current_sum
        net_cell_count = clue.length - len(assigned_cells)
        unassigned_value_sets = self.sum_to_n(net_goal_sum, net_cell_count, allowed_values)

        for unassigned_value_set in unassigned_value_sets:
            variable_set = copy.deepcopy(cell_set)
            value_set = []

            for cell in variable_set:
                if cell.value == 0:
                    value_set.append(unassigned_value_set.pop(0))
                else:
                    value_set.append(cell.value)

            value_sets.append(value_set)

        return value_sets

    def sum_to_n(self, n, k, allowed_values):
        if k == 1 and n in allowed_values:
            return [[n]]
        combos = []

        for i in allowed_values:
            allowed_values_copy = copy.deepcopy(allowed_values)
            allowed_values_copy.remove(i)

            if n - i > 0:
                combos += [[i] + combo for combo in self.sum_to_n(n - i, k - 1, allowed_values_copy)]

        for combo in combos:
            if any(combo.count(x) > 1 for x in combo):
                combos.remove(combo)

        return combos
    
    def is_consistent(self, clue, v_set, assigment):
        assigment.assign_clue(clue, v_set)
        assigment.print_board()
        return assigment.is_consistent()
    
    def recursive_BT(self, assigment):
        if assigment.is_complete() and assigment.is_consistent():
            print("Solved!")
            return assigment
        clue = self.select_unassigned_clue(assigment)
        if clue is not None:
            cell_set = assigment.get_cell(clue)
            value_sets = self.order_domain_values(clue, cell_set, assigment)

            for v_set in value_sets:
                if self.is_consistent(clue, copy.deepcopy(v_set), copy.deepcopy(assigment)):
                    assigment.assign_clue(clue, v_set)
                    assigment.print_board()
                    result = self.recursive_BT(copy.deepcopy(assigment))
                    if result is not None:
                        return result
        return None
    
    def BT_search(self, board):
        return self.recursive_BT(copy.deepcopy(board))
    
    def solve(self):
        solution = self.BT_search(self.board)
        if solution is not None:
            solution.print_board()
            board = solution
        else:
            print("No solution found!")

class IntelligentKakuroAgent(KakuroAgent):
    def __init__(self, board):
         super().__init__(board)

    def select_unassigned_clue(self, assignment):
        clue_list = []
        partial_assigned_list = []
        unassigned_list = []

        for clue in assignment.clues:
            if not assignment.is_clue_assigned(clue):
                unassigned_count = assignment.clue_unassigned_count(clue)
                if unassigned_count == clue.length:
                    unassigned_list.append((clue, unassigned_count))
                else:
                    partial_assigned_list.append((clue, unassigned_count))

        unassigned_list.sort(key=itemgetter(1))
        partial_assigned_list.sort(key=itemgetter(1))
        clue_list = partial_assigned_list + unassigned_list

        return clue_list[0][0]
    
cells = []

# 5X5 sample:
# row 1
cells.append(BlackCell((0, 0)))
cells.append(BlackCell((0, 1)))
cells.append(ClueCell((0, 2), Clue(DOWN, 4, 22), None))
cells.append(ClueCell((0, 3), Clue(DOWN, 4, 12), None))
cells.append(BlackCell((0, 4)))
# row 2
cells.append(BlackCell((1, 0)))
cells.append(ClueCell((1, 1), Clue(DOWN, 2, 15), Clue(RIGHT, 2, 12)))
cells.append(ClueCell((1, 4), Clue(DOWN, 2, 9), None))
# row 3
cells.append(ClueCell((2, 0), None, Clue(RIGHT, 4, 13)))
# row 4
cells.append(ClueCell((3, 0), None, Clue(RIGHT, 4, 29)))
# row 5
cells.append(BlackCell((4, 0)))
cells.append(ClueCell((4, 1), None, Clue(RIGHT, 2, 4)))
cells.append(BlackCell((4, 4)))

board = KakuroBoard(5, 5, cells)

intelligent_agent = IntelligentKakuroAgent(copy.deepcopy(board))

intelligent_start = timeit.default_timer()
intelligent_agent.solve()
intelligent_stop = timeit.default_timer()
intelligent_time = intelligent_stop - intelligent_start

print("Intelligent agent solved the puzzle in: \t", str(intelligent_time))

# unintelligent agent:
unintelligent_agent = KakuroAgent(copy.deepcopy(board))
unintelligent_start = timeit.default_timer()
unintelligent_stop = timeit.default_timer()
unintelligent_time = unintelligent_stop - unintelligent_start

print("Unintelligent agent solved the puzzle in:", str(unintelligent_time))