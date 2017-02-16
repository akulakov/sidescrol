#!/usr/bin/env python3
# Header {{{
import cProfile
import sys
import random
from random import random as rand

from time import sleep
from itertools import *
from avkutil import Term
# cProfile.runctx("m.dir_move('h' if rand()>0.5 else 'l')", globals(), locals())

from copy import copy
from board import Board, Loc, ModLoc, is_blocked, sizex, sizey
import board
import items
"""
Sidescrol - a side scrolling roguelike.
"""

# sizex, sizey = 79*1 + 1, 21*1 + 1
pieces = {}
player = '@'

# UTILS
rand_choice = lambda seq, default=None: random.choice(seq) if seq else default
mkrow = lambda size: [board.blank] * size
incl_range = lambda a,b: range(a, b+1)
in_order_range = lambda a,b: incl_range(*sorted((a,b)))
inverted = lambda x: int(not x)
is_even = lambda x: x%2==0
dir2coord = lambda a: 0 if is_even(a) else 1
at_dim = lambda a,b,d: (a[d], b[d])                         # values at `d` dimension
dist2 = lambda a,b: abs(a[0]-b[0])==2 or abs(a[1]-b[1])==2  # DIST=2 in one of the dimensions?
in_bounds = lambda L: (0 <= L[0] < sizex) and (0 <= L[1] < sizey)

# assuming DIST=2, return the first dimension where that is true
dist2_dim = lambda a,b: 0 if abs(a[0]-b[0])==2 else 1
dist1 = lambda a,b: abs(a[0]-b[0])==1 or abs(a[1]-b[1])==1  # DIST=1 in one of the dimensions?
same_dim_2 = lambda *a: dist2(*a) and same_dim(*a)          # ALONG same dim, DIST=2
can_move = lambda B,a,b: B[a]!=board.blank and B[b]==board.blank

next_to_both = lambda a,b,n: dist1(a,n) and dist1(b,n)      # not used
# }}}

def line(coord, loc1, loc2):
    for a in in_order_range(loc1[coord], loc2[coord]):
        opp = inverted(coord)
        yield Loc(vals={coord: a, opp: loc1[opp]})

def strjoin(seq, sep=' '):
    return sep.join(str(x) for x in seq)

class InvalidMove(Exception):
    pass
# END UTILS

class Piece:
    dirs = dict(
            l = ModLoc(1,0),
            h = ModLoc(-1,0),
            j = ModLoc(0,1),
            )

    def __init__(self, board, id, loc, is_cursor=False):
        "is_cursor: player character, board display has to follow it."
        self.board = board
        self.id=id
        self.loc = loc
        self.is_cursor = is_cursor
        self.can_dig = True
        self.descr = ''
        self.place(loc)

    def place(self, loc):
        B=self.board
        if B[loc] is board.blank:
            B[loc] = [self]
        else:
            B[loc].append(self)
        self.loc = loc
        if self.is_cursor:
            B.cursor = loc

    def remove(self, loc):
        B=self.board
        try: B[loc].remove(self)
        except ValueError as e:
            print('could not remove from %s'%str(loc))
        if not B[loc]:
            B[loc] = board.blank

    def __str__(self):
        return self.id

    def __repr__(self):
        return 'Piece %s'%self.id

    def dir_move(self, dir):
        return self.mod_move(Piece.dirs[dir])

    def mod_move(self, mod_loc):
        B=self.board
        new = self.loc[0] + mod_loc[0], self.loc[1] + mod_loc[1]
        if not in_bounds(new):
            return
        if is_blocked(B[new]):
            new = new[0], new[1]-1
            if not in_bounds(new):
                return
            if is_blocked(B[new]):
                return False
        self.move(Loc(*new))
        if self.fall():
            return False

    def move(self, new):
        if new:
            self.remove(self.loc)
            self.place(new)

    def fall(self):
        B=self.board
        fell = False
        while True:
            below = self.loc + ModLoc(0,1)
            in_bounds = lambda L: (0 <= L.x < B.sizex) and (0 <= L.y < B.sizey)
            if in_bounds(below) and not is_blocked(B[below]) and not board.ladder in B[below]:
                fell = True
                self.move(below)
            else:
                break
            if self.id == '@':
                self.board.display()
                sleep(0.1)
        return fell

    def nbr8(self):
        B=self.board
        in_bounds = lambda L: (0 <= L.x < B.sizex) and (0 <= L.y < B.sizey)
        return [Loc(*t) for t in self.loc.nbr8() if in_bounds(Loc(*t))]

    def same_side(self, item):
        return self.id.lower()==str(item).lower()

    def can_move_nbr(self):
        "Can move to this neighbour locs."
        B=self.board
        return [l for l in self.nbr8() if not self.same_side(B[l])]

    def down(self):
        self.vert(ModLoc(0,1))
    def up(self):
        self.vert(ModLoc(0,-1))

    def vert(self, mod_loc):
        B=self.board
        new = self.loc + mod_loc
        if is_blocked(B[new]):
            # dig
            B[new].remove(board.rock)
            if not B[new]:
                B[new] = board.blank
            self.fall()
        elif board.ladder in B[new]:
            self.move(new)

class Item(Piece):
    def __init__(self, *a, descr='', **kw):
        super().__init__(*a, **kw)
        self.descr = descr

class Being(Piece):
    def __init__(self, *a, health=0, is_player=False, **kw):
        self.max_health = self.health = health
        self.is_player = is_player
        self.program = None
        self.program_counter = 0
        self.inventory = {}
        super().__init__(*a, **kw)

    def mod_health(self, mod):
        # print ("in mod_health(), mod=",mod)
        self.health += mod
        if self.health <= 0:
            self.die()

    def die(self):
        # print("%s died." % self.id)
        if self.id=='@':
            sys.exit()
        self.id = '%'

    def move(self, new):
        super().move(new)
        if self.id=='@':
            descrs = list(filter(None, [x.descr for x in self.board[self.loc] if hasattr(x,'descr')]))
            if descrs:
                print("\nYou see:\n", '\n\n'.join(descrs), '\n')
                input('continue...')
        
    def fall(self):
        loc=self.loc
        super().fall()
        dist = max(self.loc.y - loc.y - 10, 0)
        self.mod_health(-dist)

    def walk(self, dir=None):
        print ("in walk()")
        if dir:
            self.program = dir
        print("self.program", self.program)
        moved = self.dir_move(self.program)
        print("moved", moved)
        if not moved:
            self.program = None

    def program_move(self):
        if not self.program or self.program_counter<=0:
            # TODO add vertical
            if self.program in ('h','l'):
                self.program = 'w'
            else:
                self.program = random.choice("hlw")
            if self.program=='w':
                self.program_counter = random.randrange(15,45)
            else:
                self.program_counter = random.randrange(15,45)
        if self.program == 'w':
            pass
        else:
            self.dir_move(self.program)
        self.program_counter -= 1

    

B=Board(sizex, sizey)
player = Being(B, '@', Loc(40,19), is_cursor=True, health=200, is_player=True)
items.add_items(Item, B, Loc)
monsters=[]
for _ in range(10000):
    loc=B.level_random_loc()
    if loc[0]<(sizex-1) and loc[1]<(sizey-1):
        B.gen_viewport(loc)
        if B[loc] is board.blank:
            monsters.append(Being(B, 'o', loc, health=10))
    
B.display()

class Sidescrol:
    def loop(self):
        t=Term()
        while True:
            if player.program:
                player.walk()
                B.display()
                print('[%s] [HP %d] ' % (player.loc, player.health))
                sleep(0.1)
                continue

            print('> ', end='')
            sys.stdout.flush()
            cmds = dict(q='quit')
            for c in "hjkl":
                cmds[c]=c
                cmds['g'+c] = 'g'+c
            inp = ''

            while True:
                inp += t.getch().decode('utf-8')
                if inp in cmds: break
                if not any(c.startswith(inp) for c in cmds):
                    print("invalid command %s, try again.." % inp)
                    inp = ''
                    break

            cmds['\n'] = None     # wait
            if inp in cmds:
                if inp=='q'  : sys.exit()
                elif inp=='j': player.down()
                elif inp=='k': player.up()
                elif inp in "hl":
                    player.dir_move(inp)
                elif inp[0]=='w' and inp[1] in "hjkl":
                    player.walk(inp[1])
                else:
                    pass

                for n, m in enumerate(monsters):
                    # if n%1000==0: print('n',n)
                    if abs(player.loc[0]-m.loc[0]) < 79*10 and abs(player.loc[1]-m.loc[1]) < 21*10:
                        # m.dir_move('h' if rand()>0.5 else 'l')
                        m.program_move()
                    elif rand()>0.95:
                        m.program_move()
                B.display()
                print('[%s] [HP %d] ' % (player.loc, player.health))

def main():
    s=Sidescrol()
    s.loop()
    for _ in range(0):
        player.dir_move('r')
        B.display()
        sleep(0.05)
main()
