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
from piece import Being, Piece, Item
import board
import items
"""
Sidescrol - a side scrolling roguelike.
"""

# sizex, sizey = 79*1 + 1, 21*1 + 1
pieces = {}
player = '@'
NUM_MONSTERS = 5000

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




B=Board(sizex, sizey)
term=Term()


items.add_items(Item, B, Loc)

monsters=[]
for _ in range(NUM_MONSTERS):
    loc=B.level_random_loc()
    if loc[0]<(sizex-1) and loc[1]<(sizey-1):
        B.gen_viewport(loc)
        if B[loc] is board.blank:
            monsters.append(Being(B, 'o', loc, health=10))

def status():
    print('[%s %s] [HP %d] [dig: %d] ' % (player.loc[0]//board.vpsize.x, player.loc[1]//board.vpsize.y, player.health,
        player.dig_points))

player = Being(B, '@', B.placeable_loc_at_vp((0,0),1), is_cursor=True, health=200, is_player=True, term=term)
B.display()
status()


class Sidescrol:
    def loop(self):
        while True:
            if player.program:
                player.walk()
                B.display()
                status()
                sleep(0.01)
                continue

            print('> ', end='')
            sys.stdout.flush()
            cmds = {'q':'quit', ',': 'pickup', 'i': 'list_inventory'}
            for c in "hjkl":
                cmds[c]=c
                cmds['g'+c] = 'g'+c
            cmds['\n'] = cmds[''] = ''     # wait

            inp = ''

            while True:
                inp += term.getch()
                if inp in cmds: break
                if inp.startswith('.'):
                    if inp.endswith('\n'):
                        inp = inp.strip()
                        break
                    continue

                if not any(c.startswith(inp) for c in cmds):
                    print("invalid command %s, try again.." % inp)
                    inp = ''
                    break

            if inp in cmds or inp.startswith('.T'):
                if inp == '':
                    pass
                elif inp=='q'  : sys.exit()
                elif inp=='j': player.down()
                elif inp=='k': player.up()
                elif inp in "hl":
                    player.dir_move(inp)
                elif inp[0]=='g' and inp[1] in "hjkl":
                    player.walk(inp[1])
                elif hasattr(player, cmds[inp]):
                    cmd = getattr(player, cmds[inp])
                    cmd()
                elif inp[:2]=='.T':
                    inp=inp[2:]
                    x,y = map(int, inp.split(','))
                    player.move((x,y))
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
                status()
                for m in B.messages:
                    print(m)
                    B.messages = []

def main():
    s=Sidescrol()
    s.loop()
    for _ in range(0):
        player.dir_move('r')
        B.display()
        sleep(0.05)
main()
