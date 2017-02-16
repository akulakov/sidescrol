from copy import copy

class Loc:
    __slots__ = tuple("xy")
    def __init__(self, x=None, y=None, vals=None):
        """`vals` is a dictionary with 0 as key for `x` and 1 as key for `y`."""
        if x is not None:
            self.x, self.y = x, y
        else:
            self.x, self.y = vals[0], vals[1]
        assert isinstance(self.x,int) and isinstance(self.y,int)

    @classmethod
    def opposite_coord(self, coord):
        return int(not coord)

    def __iter__(self):
        return iter((self.x, self.y))

    def __repr__(self):
        return '<Loc %d %d>'%(self.x,self.y)

    def __getitem__(self, i):
        return tuple(self)[i]

    def __setitem__(self, i, val):
        setattr(self, 'xy'[i], val)

    def __eq__(self, O):
        return (self.x, self.y) == (getattr(O,'x'), getattr(O,'y'))

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, mod_loc):
        l=copy(self)
        l.x, l.y = l.x + mod_loc.x, l.y + mod_loc.y
        return l

    def modified(self, coord, offset):
        new = list(self)
        new[coord] += offset
        return Loc(*new)

    def modified_at(self, coord, val):
        l = copy(self)
        l[coord] = val
        return l

    def nbr8(self):
        x,y=self
        return [(x-1,y-1),(x,y-1),(x-1,y), (x+1,y+1), (x+1,y), (x,y+1), (x-1,y+1), (x+1,y-1)]

class ModLoc(Loc):
    pass
class Size(Loc):
    pass


def test_loc():
    l=Loc(1,1)
    l=Loc(vals={0:1,1:2})
    assert l.x,l.y==(1,2)
    assert list(l)==[1,2]
    assert Loc.opposite_coord(0)==1
    assert l[1]==2
    l[1] = 3
    assert l[1]==3
    assert l.y==3
    assert l == Loc(1,3)
    assert hash(l) == hash((1,3))

    mod = l.modified(1,2)
    assert list(l)==[1,3]
    assert list(mod)==[1,5]

    mod = l.modified_at(1,6)
    assert list(mod)==[1,6]

    new = mod + ModLoc(1,1)
    assert list(new)==[2,7]

    print("test_loc(): .. PASS")

test_loc()
