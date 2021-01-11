import os
import csv
import numpy as np

os.chdir("E:/graf/test")

input_file = open("rozpady.txt", "r")
data = np.genfromtxt("rozpady.txt", delimiter = "\n")
data = data * 1000000
data_int = np.int_(data)

with open("out.csv", "w") as output_file:
    writer = csv.writer(output_file, delimiter=',')
    writer.writerows(data_int)
