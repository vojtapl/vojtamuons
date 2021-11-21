# todo: upper subplot x axis name not visible when saved as svg, time comparison, avg time for each column, save statistics to a txt file
# + show when was night

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime, timedelta
from scipy.optimize import curve_fit
from tkinter import Tk, filedialog
from csv import reader
from sys import exit


def func(x, a, b, c):
    return a * np.exp(-b * x) + c


def centers_from_borders(
    borders,
):  # https://stackoverflow.com/questions/35544233/fit-a-curve-to-a-histogram-in-python
    return borders[:-1] + np.diff(borders) / 2


# histogram settings
muon_hist_time_max = 15
muon_hist_time_min = 8
no_muon_data_bins = 20

no_time_diff_count_bins = 100
no_time_diff_ntp_bins = 100

# curve_fit histogram settings
curve_time_min = 10
# curve_time_max = 15
curve_muon_data_bins = 30

# time histogram settings
time_max_time_avg_mulitple = 1
no_muon_data_bins_time = 100

# guess
a = 1
b = 0.45
c = 1

'''
print("1 - time")
print("2 - time cutoff for ESP32")

try:
    time_setting = int(input("Select one:\n"))

except:
    print("That is not a valid option")
    raise SystemExit(0)
'''

# select directory
root = Tk()  # pointing root to Tk() to use it as Tk() in program.
root.withdraw()  # Hides small tkinter window.
root.attributes(
    "-topmost", True
)  # Opened windows will be active. above all windows despite of selection.
data_path = filedialog.askopenfilename(initialdir=os.getcwd())  # Returns opened path as str
graph_output_path = data_path[:-4] + "_graph_" # remove .csv

# open data file
with open(data_path, 'r') as input_file:
    data = list(reader(input_file)) # load data and convert to int 
data = [[int(i) for i in line] for line in data]

# moun data <-----------------------------------------------------------------changeme
## convert from clock cycles (MHz) to time (us)
#data[:] = [x / 240 for x in data]

muon_data = []
for i in range(len(data)):
    muon_data.append(data[i][0]/240) # convert to us

# compute time difference from individual time values
# time difference from cycle count of ESP32
time_diff_count = []
for i in range(len(data)-2):
    time_diff_count.append((data[i+1][1] - data[i][1])/60000000) # delta in s

# time fifference from ntp
time_diff_ntp = []
for i in range(len(data)-2):
    time_diff_ntp.append((data[i+1][2] - data[i][2])) # delta in s

'''if time_setting == 5:
    data_sorted = []
    time_diff_sorted = []
    upper_cutoff = 0
    lower_cutoff = 0

    for i in range(0, len(time_diff)):
        if time_diff[i] < upper_cutoff and time_diff[i] > lower_cutoff:
            data_sorted.append(
                data[i + 1]
            )  # +1 no need for unknow delta for first event
            time_diff_sorted.append(time_diff[i])

    print("Cut: " + str(round(len(data_sorted) / len(data) * 100, 2)) + "%")
    data = data_sorted
    time_diff = time_diff_sorted'''

# stats
print("Quantity: " + str(len(muon_data)))
print("\nMin lifetime: " + str(round(min(muon_data), 4)) + " us")
print("Max lifetime: " + str(round(max(muon_data), 4)) + " us")
print("Average lifetime: " + str(round(sum(muon_data) / len(muon_data), 4)) + " us")

print("\nMin time_diff_count: " + str(round(min(time_diff_count), 4)) + " s")
print("Max time_diff_count: " + str(round(max(time_diff_count), 4)) + " s")
print("Average time_diff_count: " + str(round(sum(time_diff_count) / len(time_diff_count), 4)) + " s")

print("\nMin time_diff_ntp: " + str(min(time_diff_ntp)) + " s")
print("Max time_diff_ntp: " + str(max(time_diff_ntp)) + " s")
print("Average time_diff_ntp: " + str(round(sum(time_diff_ntp) / len(time_diff_ntp), 4)) + " s")

# plot
fig, axs = plt.subplots(1)

# muon_data histogram
muon_data_hist, muon_data_bins = np.histogram(muon_data, bins=no_muon_data_bins, range=[muon_hist_time_min, muon_hist_time_max])

# curve fit
guess = np.array([a, b, c])
try:
    popt, pcov = curve_fit(func, centers_from_borders(muon_data_bins), muon_data_hist, guess)
except RuntimeError:
    print("Runtime error & optimal parameters not found!")
    pcov = np.array([[1, 1, 1],[1, 1, 1],[1, 1, 1]])
    popt = [1, 1, 1]
perr = np.sqrt(np.diag(pcov))

# curve_fit stats
print("\nEquation: y = ae^(-λx) + c")
print("a = " + str(round(popt[0], 2)) + "; σ_a = " + str(round(perr[0], 2)))
print("λ = " + str(round(popt[1], 4)) + "; σ_λ = " + str(round(perr[1], 5)))
print("c = " + str(round(popt[2], 2)) + "; σ_c = " + str(round(perr[2], 2)))

axs.hist(muon_data, muon_data_bins)  # plot histogram
axs.plot(muon_data_bins, func(muon_data_bins, *popt), color="darkorange", linewidth=2)  # plot fitted curve
axs.errorbar(centers_from_borders(muon_data_bins), muon_data_hist, yerr=np.sqrt(muon_data_hist), ls="none", color="black")

axs.set_xlabel("Mean lifetime (us)")
axs.set_ylabel("Number of decays")

# set minimum value (if curve_fit fails)
xmin, xmax, ymin, ymax = axs.axis()
ymin = 0
axs.axis([xmin, xmax, ymin, ymax])

# legend
axs.text(round(0.6 * xmax, 0), round(0.90 * ymax, 0), "$y = ae^{-\lambda x}+c; T_{½}\doteq $" + str(round(1 / popt[1], 4)),)

parameters = ("$a ≐ " + str(round(popt[0], 2)) + "; λ ≐ " + str(round(popt[1], 4)) + "; c ≐ " + str(round(popt[2], 2)) + "$")
axs.text(round(0.6 * xmax, 0), round(0.80 * ymax, 0), parameters, fontsize=10)

parameters_perr = ("$σ_a ≐ " + str(round(perr[0], 2)) + "; σ_λ ≐ " + str(round(perr[1], 4)) + "; σ_c ≐ " + str(round(perr[2], 2)) + "$")
axs.text(round(0.6 * xmax, 0), round(0.70 * ymax, 0), parameters_perr, fontsize=10)

plt.tight_layout(rect=[0.03, 0.03, 1, 1])
fig.savefig(graph_output_path + "muon_data.svg", format="svg")
fig.show()
plt.show()

'''
# plot time_diff_count histogram
fig, axs = plt.subplots(1)

time_diff_count_hist, time_diff_count_bins = np.histogram(time_diff_count, bins=no_time_diff_count_bins) # , range=[min(time_diff_count), time_max_time_avg_mulitple*sum(time_diff_count)/len(time_diff_count)]
axs.hist(time_diff_count, time_diff_count_bins)  
axs.set_yscale("log")

axs.set_xlabel("Time difference (count) (s)")
axs.set_ylabel("Frequency")

plt.tight_layout(rect=[0.03, 0.03, 1, 1])
fig.savefig(graph_output_path + "time_diff_count.svg", format="svg")
fig.show()
plt.show()
'''
# plot time_diff_ntp histogram
'''ime_diff_ntp_hist, time_diff_ntp_muon_data_bins = np.histogram(time_diff_ntp, bins=(round(max(time_diff_ntp))))
axs[2].hist(time_diff_ntp, time_diff_ntp_muon_data_bins)
axs[2].set_yscale("log")

axs[2].set_xlabel("Time difference (ntp) (s)")
axs[2].set_ylabel("Frequency")'''

# plot counts per time; helpful article: https://stackoverflow.com/questions/56054610/plot-histogram-of-epoch-list-x-axis-by-month-year-in-pyplot

# convert epoch to the right format for matplotlib
ntp_time = []
for i in range(len(data)):
    ntp_time.append(data[i][2])
#ntp_time = mdates.epoch2num(ntp_time)

# create bins data for histogram
min_date = datetime.fromtimestamp(min(ntp_time))
max_date = datetime.fromtimestamp(max(ntp_time))
bin_date = datetime(year = min_date.year, month = min_date.month, day = min_date.day, hour = min_date.hour, minute = 0)

ntp_time_bins = [bin_date.timestamp()]

# select time resolution
print("Select time interval of histogram's bin (please do not input unreasonable values):")
try:
    ntp_time_bin_interval_minutes = int(input(" minutes: "))
    ntp_time_bin_interval_hours = int(input(" hours: "))
    ntp_time_bin_interval_days = int(input(" days: "))
except Exception:
    print("Invalid input!")
    exit(0)

while bin_date < max_date:
    bin_date += timedelta(days = ntp_time_bin_interval_days, hours = ntp_time_bin_interval_hours, minutes = ntp_time_bin_interval_minutes)
    ntp_time_bins.append(bin_date.timestamp())

ntp_time_bins = mdates.epoch2num(ntp_time_bins)

ntp_time_plot_data = mdates.epoch2num(ntp_time)

# plot count per time histogram
fig, axs = plt.subplots(1)

#ntp_time_hist, ntp_time_bins = np.histogram(ntp_time, bins=100)
axs.hist(ntp_time_plot_data, bins = ntp_time_bins, ec = "black")
#axs.set_yscale("log")

#axs.set_xlabel("Time difference (ntp) (s)")
axs.set_ylabel("Frequency")
axs.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d.%m.%y'))
fig.autofmt_xdate()

plt.tight_layout(rect=[0.03, 0.03, 1, 1])
fig.savefig(graph_output_path + "ntp_time.svg", format="svg")
fig.show()
plt.show()