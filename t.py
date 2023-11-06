al = [[], []]
bl = [[], []]
sl = [[], [], []] 
for A in range(4):
    for B in range(4):
        a = bin(A)[2:]
        b = bin(B)[2:]
        a = '0'*(2-len(a))+a
        b = '0'*(2-len(b))+b
        s = bin(A+B)[2:]
        s = '0'*(3-len(s))+s
        al[0].append(a[0])
        al[1].append(a[1])
        bl[0].append(b[0])
        bl[1].append(b[1])
        sl[0].append(s[0])
        sl[1].append(s[1])
        sl[2].append(s[2])
for i in al:
    print(*i, sep='\n')
    print()
for i in bl:
    print(*i, sep='\n')
    print()
for i in sl:
    print(*i, sep='\n')
    print()
