import struct, os, glob
d = os.path.dirname(os.path.abspath(__file__))
for p in sorted(glob.glob(os.path.join(d, "*_*.stl"))):
    with open(p, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        mn = [1e9]*3; mx = [-1e9]*3
        for _ in range(n):
            v = struct.unpack("<12fH", f.read(50))
            for k in range(3):
                for c in range(3):
                    x = v[3 + k*3 + c]
                    mn[c] = min(mn[c], x); mx[c] = max(mx[c], x)
    print("%-20s %6.1f x %5.1f x %5.1f mm   (%d tris)" % (os.path.basename(p), mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2], n))