from random import random as rand, randrange
import random
import os

from loc import Loc, ModLoc, Size
from util import modify_loc, modify_x, modify_y, envelope
blank = ' '
rock = '#'
ladder = '+'
blocked = set([rock])
vpsize = Size(79, 21)
sizex, sizey = vpsize.x*100 + 1, vpsize.y*100 + 1
mkrow = lambda size: [blank] * size
in_bounds = lambda L: (0 <= L[0] < sizex) and (0 <= L[1] < sizey)
inverted = lambda x: int(not x)

def contains_items(B,L):
    from piece import Item
    return any(isinstance(x,Item) for x in B[L])

def is_blocked(tile):
    # print("set(tile)", set(tile))
    # print("blocked", blocked)
    # print(set(tile) & blocked)
    return tile==rock or (set(tile) & blocked)

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

def line(loc1, loc2):
    coord = int( loc1[0]==loc2[0] )
    for a in range(loc1[coord], loc2[coord]):
        opp = inverted(coord)
        yield Loc(vals={coord: a, opp: loc1[opp]})

class ModLocs:
    down = ModLoc(0,1)
    up = ModLoc(0,-1)
    right = ModLoc(1,0)
    left = ModLoc(-1,0)

class Board:
    def __init__(self, sizex, sizey, cursor=(0,0)):
        self.cursor=Loc(*cursor)
        self.sizex, self.sizey = sizex, sizey
        self.board = [mkrow(sizex) for _ in range(sizey)]
        self.generated_viewports = set()
        self.messages = []
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
            self.add_rocks(v)
            # y = v.y + vpsize[1]-1
            # for x in range(v.x, v.x+vpsize[0]+1):
            #     try: self[(x,y)] = [rock]
            #     except IndexError as e:
            #         print('err',loc,v,x,y); raise e
            #
            #     self.add_rocks_ladders(x, y)

            self.add_platforms(v)
            self.generated_viewports.add(v)

    def at_start_x(self, loc): return loc[0] == 0
    def at_start_y(self, loc): return loc[1] == 0
    def at_end_x(self, loc): return loc[0] == self.sizex-1
    def at_end_y(self, loc): return loc[1] == self.sizey-1
    def vp_bottom_right_pt(self, vp):
        return (vp[0]+vpsize[0], vp[1]+vpsize[1])

    def contains(self, loc, item):
        tile = self[loc]
        return item==tile or item in tile

    def get_first_along_line(self, start, mod_loc, item, end=None):
        # print ("in get_first_along_line(), start, modloc, item, end",start,mod_loc,item,end)
        loc = start
        while True:
            if not in_bounds(loc):
                return None
            if self.contains(loc, item):
                return loc
            if loc == end:
                return None
            loc = modify_loc(loc, mod_loc)

    def fill_rocks(self, start, end):
        for loc in line(start,end):
            self[loc] = rock

    def add_rocks(self, vp):
        # print("vp", vp)
        x = vp[0]
        y1 = y2 = base_y = vp.y + vpsize.y
        y1-=1
        if not self.at_start_x(vp):
            start = modify_x(vp, -1)
            end = modify_y(start, vpsize.y)
            first_rock = self.get_first_along_line(start, ModLocs.down, rock, end=end)
            if first_rock:
                y1 = first_rock[1]

        # print(1, modify_x(vp, vpsize.x+1))

        if in_bounds(modify_x(vp, vpsize.x+1)):
            start = modify_x(vp, vpsize.x+1)
            end = modify_y(start, vpsize.y)
            first_rock = self.get_first_along_line(start, ModLocs.down, rock, end=end)
            if first_rock:
                y2 = first_rock[1]
        y = y1
        x2 = vp[0]+vpsize[0]
        # for loc in line((x,y),(x2,y)) + line((x,y-1),(x2,y-1)):
        # self.fill_rocks((x,y),(x2,y))
        # self.fill_rocks((x,y-1),(x2,y-1))
        # self.fill_rocks((x,y-2),(x2,y-2))
        # return
        # print(3, x,x2)

        while True:
            if x>=x2 or y>base_y:
                break
            # print('!', x, (base_y), (y))
            self.fill_rocks((x,y), (x,base_y))
            x+=1
            if 0 and x2-x <= 10:
                y += 1 if y2>y else -1
            elif rand()>0.2:
                pass
            elif rand()>0.95:
                mod = randrange(2,10)
                if rand()>.5:
                    mod /= 2
                if rand()>.5:
                    mod=-mod
                y+=mod
                y=min(y, vp[1]-1)
            else:
                y+= random.choice((-1,1))

            y = envelope(y, vp.y+2, base_y-1)

    def add_platforms(self, v):
        if rand()>0.3:
            if vpsize.x-10>5 and vpsize.y-10>5:
                sx = v.x + randrange(5, vpsize.x-10)
                sy = ey = v.y + randrange(5, vpsize.y-10)
                X = vpsize.x - 5
                if X>sx:
                    ex = randrange(sx, vpsize.x-5)
                    for loc in line(Loc(sx,sy),Loc(ex,ey)):
                        # self.add(loc, rock)
                        self[loc] = rock

    def placeable_loc_at_vp(self, vp, dbg=0):
        # TODO check why this needs to be repeated....
        for _ in range(20):
            x = randrange(vp[0], vp[0]+vpsize.x+1)
            yrng = range(vp[1]+vpsize.y-1, vp[1]+1, -1)
            for y in yrng:
                if not is_blocked( self[(x,y)] ):
                    return x,y

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

    def display(self, frame=False):
        # print( self.loc)
        self.gen_viewport()
        render=lambda a: str(a[-1])
        sjoin=lambda L,sep='':sep.join(render(x) for x in L)

        v = self.viewport()
        if frame:
            print('-'*(vpsize.x+4))
        else:
            for _ in range(20): print()
        for row in self.board[v.y: v.y+vpsize[1]]:
            if frame:
                print('|', sjoin(row[v.x: v.x+vpsize[0]]), '|')
            else:
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

    def contains_items(self, L):
        from piece import Item
        return any(isinstance(x,Item) for x in self[L])

    def items(self, L):
        from piece import Item
        return [x for x in self[L] if isinstance(x,Item)]

    def at_edge(self, L):
        x,y=L
        X,Y=vpsize
        a,b = x%X in (0,X-1), y%Y == Y+1
        # if a: print(1, x%X)
        return a or b

    def add_message(self, msg):
        self.messages.append(msg)
