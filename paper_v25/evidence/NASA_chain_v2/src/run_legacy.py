from legacy import build,front,permutation
from common import read_steps
if __name__=='__main__':
    f=build(read_steps())
    front(f)
    permutation(f)
