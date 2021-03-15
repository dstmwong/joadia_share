import random

random.seed(20)

ints = []
print("randint")
for x in range(0, 20):
	ints.append(random.randint(0, 100))
print(ints)

choices = []
print("randomchoice")
list_choice = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for x in range(0, 20):
	choices.append(random.choice(list_choice))
print(choices)