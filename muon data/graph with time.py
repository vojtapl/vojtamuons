import numpy as np
import matplotlib.pyplot as plt
import os 
from scipy.optimize import curve_fit


def func(x, a, b, c):
    return a * np.exp(-b * x) + c

time_max = 40
time_min = 8
no_bins = 30

cwd = os.getcwd()
f_path = cwd + "/data/"
data_out_path = cwd + "/data_out_cropped.csv"
output_path = cwd + "/graph.svg"

os.chdir(f_path) 
if(not os.path.isfile(data_out_path)):
    data_out = open(data_out_path, "w")
    
    for i in os.listdir():
        f = open(i, "r")
        data = f.read()
        #print(data)
        print(i)
        data_out.write(data) 
        f.close()
    data_out.close()

data = np.genfromtxt(data_out_path, delimiter = ",")

#parse time and length
time = []
for i in range(len(data)):
    if (i % 2) == 1:
        time.append(data.item(i))
        np.delete(data, i)

#compute time difference from individual time values
time_diff = []
for i in range(len(time)):
    if i != (len(time) - 1):
        time_diff.append(time[i+1] - time[i])

print(time)

#convert from clock cycles (MHz) to time (us)
data = data/240

hist, bins = np.histogram(data, bins = no_bins, range = [time_min, time_max])
#bins_array = np.array(list(range(0, 100, 5)))

plt.hist(data, bins)

#bins = bins.astype(int)
popt, pcov = curve_fit(func, bins[:-1], hist)


plt.plot(bins, func(bins, *popt), color = "darkorange", linewidth = 2)

plt.xlabel("Decay (us)")
plt.ylabel("Number of decays")

#set minimum value (if curve_fit fails)
xmin, xmax, ymin, ymax = plt.axis()
ymin = 0 
plt.axis([xmin, xmax, ymin, ymax])    

# legend
plt.text(round(0.4 * xmax, 0), round(0.95 * ymax, 0), "$y = ae^{-\lambda x}+c$")

parameters = "$a = " + str(round(popt[0], 2)) + "; λ = " + str(round(popt[1], 4)) + "; c = " + str(round(popt[2], 2)) + "$"
plt.text(round(0.4 * xmax, 0), round(0.90 * ymax, 0), parameters, fontsize = 10)

perr = np.sqrt(np.diag(pcov))
parameters_perr = "$σ_a" + " = " + str(round(perr[0], 2)) + "; σ_λ = " + str(round(perr[1], 4)) + "; σ_c = " + str(round(perr[2], 2)) + "$"
plt.text(round(0.4 * xmax, 0), round(0.85 * ymax, 0), parameters_perr, fontsize = 10)


plt.savefig(output_path, format = "svg")
plt.show()