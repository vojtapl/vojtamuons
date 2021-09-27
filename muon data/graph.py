# todo: upper subplot x axis name not visible when saved as svg, time comparison, avg time for each column, save statistics to a txt file


import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.optimize import curve_fit
from tkinter import Tk, filedialog


def func(x, a, b, c):
    return a * np.exp(-b * x) + c


def centers_from_borders(
    borders,
):  # https://stackoverflow.com/questions/35544233/fit-a-curve-to-a-histogram-in-python
    return borders[:-1] + np.diff(borders) / 2


# histogram settings
time_max = 100
time_min = 8
no_bins = 30

# curve_fit histogram settings
curve_time_min = 10
# curve_time_max = 15
curve_bins = 30

# time histogram settings
time_max_time_avg_mulitple = 1
no_bins_time = 100

# guess
a = 1
b = 0.45
c = 1


print("1 - no time")
print("2 - ESP32 time")
print("3 - epoch time")
print("4 - time comparison mode (scrapped for now)")
print("5 - experimental time cutoff for ESP32")

try:
    time_setting = int(input("Select one:\n"))

except:
    print("That is not a valid option")
    raise SystemExit(0)

if time_setting == 4:
    exec(open("time_comparison.py").read())
    raise SystemExit(0)


root = Tk()  # pointing root to Tk() to use it as Tk() in program.
root.withdraw()  # Hides small tkinter window.
root.attributes(
    "-topmost", True
)  # Opened windows will be active. above all windows despite of selection.
cwd = filedialog.askdirectory(initialdir=os.getcwd())  # Returns opened path as str

f_path = cwd + "/data/"
data_out_path = cwd + "/data.csv"
graph_output_path = cwd + "/graph.svg"


if os.path.exists(data_out_path) == False:
    # convert all files in ./data/ to data.csv
    os.chdir(f_path)
    if not os.path.isfile(data_out_path):
        data_out = open(data_out_path, "w")

        for i in os.listdir():
            f = open(i, "r")
            file_data = f.read()
            # print(file_data)
            print(i)
            data_out.write(file_data)
            f.close()
            data_out.close()

# open data.csv
np_data = np.genfromtxt(data_out_path, delimiter=",")

if time_setting == 2 or 3 or 5:
    # parse time and length
    data = []
    time = []
    for i in range(len(np_data)):
        if (i % 2) == 0:
            data.append(np_data.item(i))
        if (i % 2) == 1:
            time.append(np_data.item(i))

    # compute time difference from individual time values
    time_diff = []
    if time_setting == 2 or 5:
        for i in range(len(time) - 1):
            time_diff.append((time[i + 1] - time[i]) / 60000000)  # delta in minutes
    if time_setting == 3:
        for i in range(len(time) - 1):
            time_diff.append((time[i + 1] - time[i]) / 60)  # delta in minutes
    if time_setting == 5:
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
        time_diff = time_diff_sorted

if time_setting == 1:
    data = list(np_data)

# convert from clock cycles (MHz) to time (us)
data[:] = [x / 240 for x in data]


hist, bins = np.histogram(data, bins=no_bins, range=[time_min, time_max])

# curve fit
guess = np.array([a, b, c])
popt, pcov = curve_fit(func, centers_from_borders(bins), hist, guess)
perr = np.sqrt(np.diag(pcov))

# timeless plot w/o subplots
if time_setting == 1:
    print("Quantity:" + str(len(data)))
    print("\nMin lifetime: " + str(min(data)))
    print("Max lifetime: " + str(max(data)))
    print("Average lifetime: " + str(sum(data) / len(data)))

    print("\nEquation: y = ae^(-λx) + c")
    print("a = " + str(round(popt[0], 2)) + "; σ_a = " + str(round(perr[0], 2)))
    print("λ = " + str(round(popt[1], 4)) + "; σ_λ = " + str(round(perr[1], 4)))
    print("c = " + str(round(popt[2], 2)) + "; σ_c = " + str(round(perr[2], 2)))

    plt.hist(data, bins)  # plot histogram
    plt.plot(
        bins, func(bins, *popt), color="darkorange", linewidth=2
    )  # plot fitted curve
    axs[0].errorbar(
        centers_from_borders(bins), hist, yerr=np.sqrt(hist), ls="none", color="black"
    )

    plt.xlabel("Mean lifetime (us)")
    plt.ylabel("Number of decays")

    # set minimum value (if curve_fit fails)
    xmin, xmax, ymin, ymax = plt.axis()
    ymin = 0
    plt.axis([xmin, xmax, ymin, ymax])

    # legend
    axs[0].text(
        round(0.4 * xmax, 0),
        round(0.90 * ymax, 0),
        "$y = ae^{-\lambda x}+c; T_{½}\doteq $" + str(round(1 / popt[1], 4)),
    )

    parameters = (
        "$a ≐ "
        + str(round(popt[0], 2))
        + "; λ ≐ "
        + str(round(popt[1], 4))
        + "; c ≐ "
        + str(round(popt[2], 2))
        + "$"
    )
    plt.text(round(0.4 * xmax, 0), round(0.80 * ymax, 0), parameters, fontsize=10)

    parameters_perr = (
        "$σ_a"
        + " ≐ "
        + str(round(perr[0], 2))
        + "; σ_λ ≐ "
        + str(round(perr[1], 4))
        + "; σ_c ≐ "
        + str(round(perr[2], 2))
        + "$"
    )
    plt.text(round(0.4 * xmax, 0), round(0.70 * ymax, 0), parameters_perr, fontsize=10)

    plt.tight_layout(rect=[0.03, 0.03, 1, 1])
    plt.savefig(graph_output_path, format="svg")
    plt.show()
    plt.show()

# plot with time
elif time_setting == 2 or 3 or 5:
    print("Quantity:" + str(len(data)))
    print("\nMin lifetime: " + str(min(data)))
    print("Max lifetime: " + str(max(data)))
    print("Average lifetime: " + str(sum(data) / len(data)))

    print("\nMin time_diff: " + str(min(time_diff)))
    print("Max time_diff: " + str(max(time_diff)))
    print("Average time_diff: " + str(sum(time_diff) / len(time_diff)))

    print("\nEquation: y = ae^(-λx) + c")
    print("a = " + str(round(popt[0], 2)) + "; σ_a = " + str(round(perr[0], 2)))
    print("λ = " + str(round(popt[1], 4)) + "; σ_λ = " + str(round(perr[1], 4)))
    print("c = " + str(round(popt[2], 2)) + "; σ_c = " + str(round(perr[2], 2)))

    # time histogram
    time_hist, time_bins = np.histogram(
        time_diff,
        bins=no_bins_time,
        range=[
            min(time_diff),
            time_max_time_avg_mulitple * sum(time_diff) / len(time_diff),
        ],
    )

    fig, axs = plt.subplots(2)

    axs[0].hist(data, bins)  # plot histogram
    axs[0].plot(
        bins, func(bins, *popt), color="darkorange", linewidth=2
    )  # plot fitted curve
    axs[0].errorbar(
        centers_from_borders(bins), hist, yerr=np.sqrt(hist), ls="none", color="black"
    )
    axs[1].hist(time_diff, time_bins)  # plot time histogram
    axs[1].set_yscale("log")

    axs[0].set_xlabel("Mean lifetime (us)")
    axs[0].set_ylabel("Number of decays")
    axs[1].set_xlabel("Time difference (min)")
    axs[1].set_ylabel("Frequency")

    # set minimum value (if curve_fit fails)
    xmin, xmax, ymin, ymax = axs[0].axis()
    ymin = 0
    axs[0].axis([xmin, xmax, ymin, ymax])

    # legend
    axs[0].text(
        round(0.4 * xmax, 0),
        round(0.90 * ymax, 0),
        "$y = ae^{-\lambda x}+c; T_{½}\doteq $" + str(round(1 / popt[1], 4)),
    )

    parameters = (
        "$a ≐ "
        + str(round(popt[0], 2))
        + "; λ ≐ "
        + str(round(popt[1], 4))
        + "; c ≐ "
        + str(round(popt[2], 2))
        + "$"
    )
    axs[0].text(round(0.4 * xmax, 0), round(0.80 * ymax, 0), parameters, fontsize=10)

    parameters_perr = (
        "$σ_a ≐ "
        + str(round(perr[0], 2))
        + "; σ_λ ≐ "
        + str(round(perr[1], 4))
        + "; σ_c ≐ "
        + str(round(perr[2], 2))
        + "$"
    )
    axs[0].text(
        round(0.4 * xmax, 0), round(0.70 * ymax, 0), parameters_perr, fontsize=10
    )

    plt.tight_layout(rect=[0.03, 0.03, 1, 1])
    fig.savefig(graph_output_path, format="svg")
    fig.show()
    plt.show()
