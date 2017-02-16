from random import random as rand, randrange
import random
import os

from loc import Loc, ModLoc, Size
blank = ' '
rock = '#'
ladder = '+'
blocked = set([rock])
vpsize = Size(79, 21)
sizex, sizey = vpsize.x*100 + 1, vpsize.y*100 + 1
mkrow = lambda size: [blank] * size

def is_blocked(tile):
    # print("set(tile)", set(tile))
    # print("blocked", blocked)
    # print(set(tile) & blocked)
    return set(tile) & blocked

def test_is_blocked():
    assert is_blocked(['#'])
    assert is_blocked(['#','a'])
    assert not is_blocked(['a'])
    assert not is_blocked(blank)
test_is_blocked()


# def line(coord, loc1, loc2):
#     for a in in_order_range(loc1[coord], loc2[coord]):
#         opp = inverted(coord)
#         yield Loc(vals={coord: a, opp: loc1[opp]})

inverted = lambda x: int(not x)
def line(loc1, loc2):
    coord = int( loc1[0]==loc2[0] )
    for a in range(loc1[coord], loc2[coord]):
        opp = inverted(coord)
        yield Loc(vals={coord: a, opp: loc1[opp]})

class Board:
    def __init__(self, sizex, sizey, cursor=(0,0)):
        self.cursor=Loc(*cursor)
        self.sizex, self.sizey = sizex, sizey
        self.board = [mkrow(sizex) for _ in range(sizey)]
        self.generated_viewports = set()
        self.gen_viewport()

    def in_generated_viewport(self, loc):
        return self.viewport(loc) in self.generated_viewports

    def viewport(self, loc=None):
        "Current viewport based on `self.loc`"
        L= loc or self.cursor
        return Loc(L[0] - (L[0] % vpsize[0]), L[1] - (L[1] % vpsize[1]))

    def gen_viewport(self, loc=None):
        v=self.viewport(loc)
        if v not in self.generated_viewports:
            y = v.y + vpsize[1]-1
            for x in range(v.x, v.x+vpsize[0]+1):
                try: self[(x,y)] = [rock]
                except IndexError as e:
                    print('err',loc,v,x,y); raise e

                self.add_rocks_ladders(x, y)

            self.add_platforms(v)
            self.generated_viewports.add(v)

    def add_platforms(self, v):
        if rand()>0.3:
            sx = v.x + randrange(5, vpsize.x-10)
            sy = ey = v.y + randrange(5, vpsize.y-10)
            X = vpsize.x - 5
            if X>sx:
                ex = randrange(sx, vpsize.x-5)
                for loc in line(Loc(sx,sy),Loc(ex,ey)):
                    self.add(loc, rock)

    def add_rocks_ladders(self, x, y):
        if rand()>0.95:
            self[(x,y-1)] = [rock]
            if rand()>0.75:
                self[(x,y-2)] = [rock]
        elif rand()>0.98:
            h = randrange(2, vpsize.y-3)
            for loc in line((x,y-h-2), (x,y)):
                self[loc] = [ladder]

    def add(self, loc, item):
        if item is blank:
            self[loc] = blank
        elif self[loc] is blank:
            self[loc] = [item]
        else:
            self[loc].append(item)

    def __iter__(self):
        for y in range(sizey):
            for x in range(sizex):
                yield Loc(x,y)

    def __setitem__(self, loc, val):
        self.board[loc[1]][loc[0]] = val

    def __getitem__(self, loc):
        return self.board[loc[1]][loc[0]]

    def setitems(self, locs, val):
        for l in locs:
            self[l] = val

    def add_piece(self, id, *locs):
        locs = [Loc(*a) for a in locs]
        pieces[id] = Piece(id, *locs)
        for l in locs:
            self[l] = id

    def display(self):
        # print( self.loc)
        self.gen_viewport()
        render=lambda a: str(a[-1])
        sjoin=lambda L,sep='':sep.join(render(x) for x in L)

        v = self.viewport()
        for _ in range(20): print()
        for row in self.board[v.y: v.y+vpsize[1]]:
            print(sjoin(row[v.x: v.x+vpsize[0]]))
        print()

    def check_valid(self, loc1, loc2):
        assert self[loc2]==blank
        assert self[loc1]!=blank

    def cols(self):
        pass

    def fall(self):
        # empty-below: return first matching or None next(filter(), None)
        # for each COL: top piece, check if it needs processing,
        # cols = for each x, range(0,sizey)
        # col = [Loc(x,y) for y in range(0,sizey)]
        # pieces = reversed(loc for loc in loc if self[loc] is not blank)
        # for P in pieces: below = loc.modified(1,1); if below is blank OR opposing: move below

        mkcol = lambda x: [Loc(x,y) for y in range(self.sizey)]
        notblank = lambda loc: self[loc] is not blank
        same_side = lambda a,b: self[a].id.lower() == self[b].id.lower()
        diff_side = lambda a,b: not same_side(a,b)
        in_bounds = lambda L: (0 <= L.x < self.sizex) and (0 <= L.y < self.sizey)
        can_move = lambda a,b: in_bounds(b) and (self[b] is blank or diff_side(a,b))

        cols = [mkcol(x) for x in range(self.sizex)]
        below = lambda L: L.modified(1,1)
        moved=None
        n=0
        while moved != 0:
            moved=0
            for col in cols[:]:
                n+=1
                pieces = list(reversed([loc for loc in col if self[loc] is not blank]))
                for loc in pieces[:]:
                    if can_move(loc, below(loc)):
                        p=self[loc]; new=below(loc)
                        p.move(new); moved+=1
            if n>50: break

    def random_move(self):
        for l in self:
            if not self[l] is blank:
                self[l].move( rand_choice(self[l].can_move_nbr()) )

    def random_loc(self):
        return randrange(0, self.sizex), randrange(0, self.sizey)

    def level_random_loc(self):
        y= randrange(0, self.sizey)
        y=y-y%vpsize[1]-2
        return randrange(0, self.sizex), y

    def random_blank(self):
        while True:
            x,y = randrange(0, self.sizex), randrange(0, self.sizey)
            if self[(x,y)] is blank:
                return x,y
