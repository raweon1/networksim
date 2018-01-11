class Package(object):
    id = 1

    def __init__(self):
        self.id = Package.id
        Package.id += 1


print(Package.id)
print(Package().id)
print(Package.id)
