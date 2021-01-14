#todo: graph time, time comparison, avg time for each column
import numpy as np
import matplotlib.pyplot as plt
import os 
from scipy.optimize import curve_fit


def func(x, a, b, c):
    return a * np.exp(-b * x) + c


time_max = 100
time_min = 8
no_bins = 30

curve_time_min = 8
curve_bins = 30

time_max_time_avg_mulitple = 1
no_bins_time = 100

#guess
a = 1
b = 0.45
c = 1


cwd = os.getcwd()
f_path = cwd + "/data/"
data_out_path = cwd + "/data.csv"
graph_output_path = cwd + "/graph.svg"

print("1 - no time")
print("2 - ESP32 time")
print("3 - epoch time")
print("4 - time comparison mode")
try:
    time_setting = int(input("Select one\n"))

except:
    print("That is not a valid option")
    raise SystemExit(0)
    
if(time_setting == 4):
    exec(open("time_comparison.py").read())
    raise SystemExit(0)
    
    
if(os.path.exists(data_out_path) == False):
    #convert all files in ./data/ to data.csv
    os.chdir(f_path) 
    if(not os.path.isfile(data_out_path)):
        data_out = open(data_out_path, "w")
    
        for i in os.listdir():
            f = open(i, "r")
            file_data = f.read()
            #print(file_data)
            print(i)
            data_out.write(file_data) 
            f.close()
            data_out.close()

#open data.csv
np_data = np.genfromtxt(data_out_path, delimiter = ",")

if(time_setting == 2 or 3):
    #parse time and length
    data = []
    time = []
    for i in range(len(np_data)):
        if((i % 2) == 0):
            data.append(np_data.item(i))
        if((i % 2) == 1):
            time.append(np_data.item(i))
            
    #compute time difference from individual time values
    time_diff = []
    if(time_setting == 2):
        for i in range(len(time) - 1):
            time_diff.append((time[i+1] - time[i])/60000000) #delta in minutes      
    if(time_setting == 3):    
        for i in range(len(time) - 1):
            time_diff.append((time[i+1] - time[i])/60) #delta in minutes

if(time_setting == 1):
    data = list(np_data)

#convert from clock cycles (MHz) to time (us)
data[:] = [x / 240 for x in data]
  
hist, bins = np.histogram(data, bins = no_bins, range = [time_min, time_max])
#bins_array = np.array(list(range(0, 100, 5)))


#bins = bins.astype(int)

#curve fit
curve_hist, curve_bins = np.histogram(data, bins = curve_bins, range = [curve_time_min, time_max])
guess = np.array([a, b, c])
popt, pcov = curve_fit(func, curve_bins[:-1], curve_hist, guess)
perr = np.sqrt(np.diag(pcov))

#timeless plot w/o subplots
if(time_setting == 1):
    print("Quantity:" + str(len(data)))
    print("\nMin lifetime: " + str(min(data)))
    print("Max lifetime: " + str(max(data)))
    print("Average lifetime: " + str(sum(data)/len(data)))
    
    print("\nEquation: y = ae^(-λx) + c")
    print("a = " + str(round(popt[0], 2)) + "; σ_a = " + str(round(perr[0], 2)))
    print("λ = " + str(round(popt[1], 4)) + "; σ_λ = " + str(round(perr[1], 4)))
    print("c = " + str(round(popt[2], 2)) + "; σ_c = " + str(round(perr[2], 2)))    
    
    plt.hist(data, bins) #plot histogram
    plt.plot(bins, func(bins, *popt), color = "darkorange", linewidth = 2) #plot fitted curve
    
    plt.xlabel("Mean lifetime (us)")
    plt.ylabel("Number of decays")
    
    #set minimum value (if curve_fit fails)
    xmin, xmax, ymin, ymax = plt.axis()
    ymin = 0 
    plt.axis([xmin, xmax, ymin, ymax])    
    
    # legend
    plt.text(round(0.4 * xmax, 0), round(0.95 * ymax, 0), "$y = ae^{-\lambda x}+c$")
    
    parameters = "$a = " + str(round(popt[0], 2)) + "; λ = " + str(round(popt[1], 4)) + "; c = " + str(round(popt[2], 2)) + "$"
    plt.text(round(0.4 * xmax, 0), round(0.90 * ymax, 0), parameters, fontsize = 10)
    
    parameters_perr = "$σ_a" + " = " + str(round(perr[0], 2)) + "; σ_λ = " + str(round(perr[1], 4)) + "; σ_c = " + str(round(perr[2], 2)) + "$"
    plt.text(round(0.4 * xmax, 0), round(0.85 * ymax, 0), parameters_perr, fontsize = 10)
    
    
    plt.savefig(graph_output_path, format = "svg")
    plt.show()

#plot with time
if(time_setting == 2 or 3):
    print("Quantity:" + str(len(data)))
    print("\nMin lifetime: " + str(min(data)))
    print("Max lifetime: " + str(max(data)))
    print("Average lifetime: " + str(sum(data)/len(data)))
    
    print("\nMin time_diff: " + str(min(time_diff)))
    print("Max time_diff: " + str(max(time_diff)))
    print("Average time_diff: " + str(sum(time_diff)/len(time_diff)))

    print("\nEquation: y = ae^(-λx) + c")
    print("a = " + str(round(popt[0], 2)) + "; σ_a = " + str(round(perr[0], 2)))
    print("λ = " + str(round(popt[1], 4)) + "; σ_λ = " + str(round(perr[1], 4)))
    print("c = " + str(round(popt[2], 2)) + "; σ_c = " + str(round(perr[2], 2)))    

    #time histogram
    time_hist, time_bins = np.histogram(time_diff, bins = no_bins_time, range = [min(time_diff), time_max_time_avg_mulitple * sum(time_diff)/len(time_diff)])
    
    fig, axs = plt.subplots(2)
    
    axs[0].hist(data, bins) #plot histogram
    axs[0].plot(bins, func(bins, *popt), color = "darkorange", linewidth = 2) #plot fitted curve
    axs[1].hist(time_diff, time_bins) #plot time histogram
    
    axs[0].set_xlabel("Mean lifetime (us)")
    axs[0].set_ylabel("Number of decays")   
    axs[1].set_xlabel("Time difference (min)")
    axs[1].set_ylabel("Frequency")
    
    #set minimum value (if curve_fit fails)
    xmin, xmax, ymin, ymax = axs[0].axis()
    ymin = 0 
    axs[0].axis([xmin, xmax, ymin, ymax])    
    
    # legend
    axs[0].text(round(0.4 * xmax, 0), round(0.95 * ymax, 0), "$y = ae^{-\lambda x}+c$")
    
    parameters = "$a = " + str(round(popt[0], 2)) + "; λ = " + str(round(popt[1], 4)) + "; c = " + str(round(popt[2], 2)) + "$"
    axs[0].text(round(0.4 * xmax, 0), round(0.90 * ymax, 0), parameters, fontsize = 10)
    
    parameters_perr = "$σ_a = " + str(round(perr[0], 2)) + "; σ_λ = " + str(round(perr[1], 4)) + "; σ_c = " + str(round(perr[2], 2)) + "$"
    axs[0].text(round(0.4 * xmax, 0), round(0.85 * ymax, 0), parameters_perr, fontsize = 10)
    
    fig.savefig(graph_output_path, format = "svg")
    fig.show()