import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_sleeve import helix_sleeve, write_binary_stl
v, f = helix_sleeve(slit=2.0, length=20.0)
write_binary_stl(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_preview20.stl'), v, f, b'preview20')
print('ok')
