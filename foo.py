tmp = {1: "1", 2: "2"}

print(tmp.keys())
del tmp[1]
print(tmp.keys())
print(tmp)
try:
    tmp[1]
except KeyError:
    print("ok")
