from stats import Stats
from numpy import *

stats = Stats()

a = zeros(10000000)
print(stats.time())
print(stats.memory())
a = sin(a)
print(stats.time())
print(stats.memory())
a = cos(a)
print(stats.time())
print(stats.memory())
a = cos(a)**2+sin(a)**2
print(stats.time())
print(stats.memory())


