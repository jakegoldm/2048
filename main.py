from typing import List, Callable, Any
from enum import Enum
from copy import deepcopy
from math import log2
import random as rd
import sys
import os 

COLOR_SHIFT = 40
MAX_COLOR = 46

class Direction(Enum): 
    UP = 1
    LEFT = 2 
    DOWN = 3 
    RIGHT = 4

DIR_TABLE = {
    'w': Direction.UP,
    's': Direction.DOWN,
    'd': Direction.RIGHT,
    'a': Direction.LEFT,
}


class Block: 
    width: int = 6
    empty_val: int = 0
    empty_val_str: str = " " * width

    def __init__(self):
        self.val = self.empty_val

    def new_val(self): 
        self.val = rd.randint(1, 2) * 2

    def is_empty(self): 
        return self.val == self.empty_val
    
    def clear(self): 
        self.val = self.empty_val
    
    def get_val(self): 
        return self.val
    
    def stringify_val(self): 
        val = ""
        if not self.is_empty(): 
            s = str(self.val)
            spaces = self.width - len(s)
            pos = int(spaces / 2)
            val += " " * pos
            val += s 
            val += " " * (self.width - len(s) - pos)
        else: 
            val = self.empty_val_str
        return val


class Grid:  
    def __init__(self, n: int=4, init_blocks: int=2, 
                 blocks_per_round: List[int]=[1, 1, 1, 2], colors=False): 
        self.grid: List[Block] = []
        for _ in range(n ** 2): 
            self.grid.append(Block())
        self.n = n
        self.init_blocks = init_blocks
        self.bpr = blocks_per_round
        self.shift_map = {
            # Direction -> (flat shift indices, order to traverse grid, check if valid index)
            Direction.UP    : (-self.n, range(self.n ** 2),             lambda x: x >= 0), 
            Direction.LEFT  : (-1,      range(self.n ** 2),             lambda x: (x + 1) % self.n != 0),
            Direction.DOWN  : (self.n,  range(self.n ** 2 - 1, -1, -1), lambda x: x < self.n ** 2),
            Direction.RIGHT : (1,       range(self.n ** 2 - 1, -1, -1), lambda x: x % self.n != 0)
        }
        self.colors = colors
        self.to_flat = lambda r, c: r * n + c
        self.make_new_blocks(init_blocks)

    def _available(self, pos: int, bound_check: Callable[[int], bool]): 
        return bound_check(pos) and self.grid[pos].is_empty()
    
    def _plaintext_disp(self):
        line = disp = "+" + ("-" * Block.width + "+") * self.n + "\n"
        for r in range(self.n):
            for i in range(int(Block.width / 2)): 
                for c in range(self.n): 
                    block: Block = self.grid[self.to_flat(r, c)]
                    val = block.stringify_val() if i == int(Block.width / 4) else Block.empty_val_str
                    disp += f"|{val}"
                disp += "|\n"
            disp += line
        return disp
    
    def _colored_disp(self): 
        line = disp = "\033[107m " + (" " * Block.width + " ") * self.n + "\033[0m\n"
        for r in range(self.n):
            for i in range(int(Block.width / 2)): 
                for c in range(self.n): 
                    block: Block = self.grid[self.to_flat(r, c)]
                    val_str = block.stringify_val() if i == int(Block.width / 4) else Block.empty_val_str
                    block_val = block.get_val()
                    color_norm = (int(log2(block_val)) if block_val else 0) + COLOR_SHIFT
                    disp += f"\033[107m \033[0;37;{min(color_norm, MAX_COLOR)}m{val_str}\033[0m"
                disp += "\033[107m \033[0m\n"
            disp += line
        return disp        

    def _shift(self, dir: Direction): 
        fs, iterator, bound_check = self.shift_map[dir]
        for i in iterator: 
            if self.grid[i].is_empty(): 
                continue
            old_pos = i
            new_pos = i + fs
            while self._available(new_pos, bound_check): 
                self.grid[new_pos] = deepcopy(self.grid[old_pos])
                self.grid[old_pos].clear()
                old_pos = new_pos
                new_pos = new_pos + fs

    def _collapse(self, dir: Direction): 
        fs, iterator, bound_check = self.shift_map[dir]
        for i in iterator: 
            if bound_check(i + fs) and self.grid[i].val == self.grid[i + fs].val:
                self.grid[i + fs].val *= 2
                self.grid[i].clear()

    def make_new_blocks(self, num_blocks): 
        rd_pos = lambda: rd.choice(range(self.n ** 2))
        for _ in range(num_blocks): 
            if sum(map(Block.is_empty, self.grid)) == 0:
                return
            pos = rd_pos()
            while not self.grid[pos].is_empty(): 
                pos = rd_pos()
            self.grid[pos].new_val()

    def shift_and_collapse(self, dir: Direction): 
        self._shift(dir)
        self._collapse(dir)
        self._shift(dir)
                    
    def is_game_over(self): 
        for i in range(self.n ** 2): 
            if self.grid[i].is_empty(): 
                return False 
            val = self.grid[i].val
            if i % self.n != 0 and self.grid[i - 1].val == val:
                return False
            if (i + 1) % self.n != 0 and self.grid[i + 1].val == val: 
                return False
            if i >= self.n and self.grid[i - self.n].val == val: 
                return False
            if i < self.n * (self.n - 1) and self.grid[i + self.n].val == val: 
                return False
        return True

    def get_display(self): 
        return self._colored_disp() if self.colors else self._plaintext_disp()

    def get_score(self): 
        return sum(map(Block.get_val, self.grid))
    

class GameLoop: 
    def __init__(self, g: Grid, disp_func: Callable[[Any], None]=print): 
        self.g = g
        self.disp_func = disp_func

    def _get_dir(self):
        dir = ""
        while dir not in DIR_TABLE: 
            dir = input("Enter Direction: ").lower()
            if dir == 'q': 
                sys.exit()
        return DIR_TABLE[dir]
    
    def run(self): 
        while not self.g.is_game_over(): 
            self.disp_func(self.g.get_display())
            dir = self._get_dir()
            self.g.shift_and_collapse(dir)
            self.g.make_new_blocks(rd.choice(self.g.bpr))
            os.system("clear")
        self.disp_func(self.g.get_display())
        score = self.g.get_score()
        self.disp_func(f"GAME OVER! score = {score}")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# WASD-controlled 2048 in Python!
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def main(): 
    g = Grid(colors=True)
    loop = GameLoop(g)
    loop.run()

if __name__ == "__main__":
    main()
