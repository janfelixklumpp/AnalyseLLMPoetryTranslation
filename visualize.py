import matplotlib.pyplot as plt
import random
import csv
from scipy.stats import bootstrap
import numpy as np

plt.rcParams.update({'axes.labelsize': 15})
plt.rcParams.update({'xtick.labelsize': 15})
plt.rcParams.update({'ytick.labelsize': 15})

def get_mean(v, x):
    return np.mean(v)

filenames = ["results.csv"] # names of files containing the results

# the tags of the relevant conditions in the result files
tags = ["deepl","george","tieck","regis","wolff","walesrode","gpt4o_plain","gpt4o_plainform","gpt4o_plainmeaning","gemini_plain","gemini_plainform","gemini_plainmeaning","claude_plain","claude_plainform","claude_plainmeaning","o4mini_plain","o4mini_plainform","o4mini_plainmeaning","gpt5_plain","gpt5_plainform","gpt5_plainmeaning"]
#tags = ["deepl","george","tieck","regis","wolff","walesrode","gpt4o_plain","gpt4o_plainform","gpt4o_plainmeaning","gpt4o_iterativeform","gpt4o_iterativemeaning","gpt4o_iterativemixed","gpt4o_iterform2steps","gpt4o_analysistranslate","gpt4o_analysisrewrite"]

# markers (for average values)
markers = ["o","o","o","o","o","o","o","o","o","^","^","^","s","s","s","P","P","P","X","X","X"]
#markers = ["o","o","o","o","o","o","o","o","o","o","o","o","o","o","o"]

# marker sizes (for average values)
markersizes = [6,6,6,6,6,6,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]
#markersizes = [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6]

# colors
colors = ["black","grey","grey","grey","grey","grey","red","gold","deepskyblue","red","gold","deepskyblue","red","gold","deepskyblue","darkred","darkorange","darkblue","firebrick","goldenrod","royalblue"]
#colors = ["black","grey","grey","grey","grey","grey","red","gold","deepskyblue","darkorange","darkblue","green","darkgoldenrod","hotpink","darkviolet",]

# labels in the legend
labels = ["DeepL", "Human", None, None, None, None, "GPT-4o: Plain", "   PlainForm", "   PlainMeaning", "Gemini 1.5: Plain", "   PlainForm", "   PlainMeaning", "Claude 3.5 Sonnet: Plain",
           "   PlainForm", "   PlainMeaning", "OpenAI o4-mini: Plain",  "   PlainForm", "   PlainMeaning", "GPT-5: Plain", "   PlainForm", "   PlainMeaning"]
#labels = ["DeepL", "Human", None, None, None, None, "GPT-4o: Plain", "   PlainForm", "   PlainMeaning", "   IterativeForm", "   IterativeMeaning", "   IterativeMixed",
#          "   IterForm2Steps", "   AnalysisTranslate", "   AnalysisRewrite"]

type = "average_values" # "average_values" or "points", depending on whether averages or individual poems shall be visualized
plot_besides = True # plot metre and rhyme next to each other

results = []
for fn in filenames:
    for l in csv.reader(open(f"{fn}","r")):
        if 'None' not in l and 'translator' not in l: # unless one of the metrics is undefined or the line is the header
            results.append([l[0], int(l[1]), float(l[2]), float(l[3]), float(l[4])])
# convert to dictionary
data = {} # dictionary with lists of triples as values: key: tag, value: [(Bert score, metre, rhyme)]
for tag in tags:
    data[tag] = []
for r in results:
    if r[0] in tags:
        data[r[0]].append((r[2],r[3],r[4]))

if plot_besides:
    plt.subplots(1, 2)
    plt.subplot(1, 2, 1)

if type == "average_values":
    # get average values and bootstrap confidence intervals
    means_cometkiwi = [np.mean([r[0] for r in data[c]]) for c in tags]
    means_metre = [np.mean([r[1] for r in data[c]]) for c in tags]
    means_rhyme = [np.mean([r[2] for r in data[c]]) for c in tags]
    boot_cometkiwi = [bootstrap(([r[0] for r in data[c]], [0 for r in data[c]]), get_mean, method="basic") for c in tags]
    boot_metre = [bootstrap(([r[1] for r in data[c]], [0 for r in data[c]]), get_mean, method="basic") for c in tags]
    boot_rhyme = [bootstrap(([r[2] for r in data[c]], [0 for r in data[c]]), get_mean, method="basic") for c in tags]

    plt.gca().invert_xaxis()

    # visualize metrical distance
    for i in range(len(tags)):
        metre_mean = np.mean(boot_metre[i].bootstrap_distribution)
        cometkiwi_mean = np.mean(boot_cometkiwi[i].bootstrap_distribution)
        xerr = [[metre_mean - boot_metre[i].confidence_interval[0]], [boot_metre[i].confidence_interval[1] - metre_mean]]
        yerr = [[cometkiwi_mean - boot_cometkiwi[i].confidence_interval[0]], [boot_cometkiwi[i].confidence_interval[1] - cometkiwi_mean]]
        plt.errorbar(metre_mean, cometkiwi_mean, xerr=xerr, yerr=yerr, fmt=markers[i], color=colors[i], label=labels[i], markersize=markersizes[i])
        plt.ylabel("CometKiwi", fontsize=24)
        plt.xlabel("Metrical distance", fontsize=24)
        legend = plt.legend(ncol=2, prop={'size': 15})
    if not plot_besides:
        plt.show()
    else:
        plt.subplot(1, 2, 2)

    # visualize rhyme scheme similarities
    for i in range(len(tags)):
        rhyme_mean = np.mean(boot_rhyme[i].bootstrap_distribution)
        cometkiwi_mean = np.mean(boot_cometkiwi[i].bootstrap_distribution)
        xerr = [[rhyme_mean - boot_rhyme[i].confidence_interval[0]], [boot_rhyme[i].confidence_interval[1] - rhyme_mean]]
        yerr = [[cometkiwi_mean - boot_cometkiwi[i].confidence_interval[0]], [boot_cometkiwi[i].confidence_interval[1] - cometkiwi_mean]]
        plt.errorbar(rhyme_mean, cometkiwi_mean, xerr=xerr, yerr=yerr, fmt=markers[i], color=colors[i], label=labels[i], markersize=markersizes[i])
        plt.ylabel("CometKiwi", fontsize=24)
        plt.xlabel("Rhyme scheme similarity", fontsize=24)
        legend = plt.legend(ncol=2, prop={'size': 15})
    plt.show()

elif type == "points":
    plt.gca().invert_xaxis()

    # visualize metrical distance
    for i in range(len(tags)):
        plt.scatter([x[1] for x in data[tags[i]]], [y[0] for y in data[tags[i]]], c=colors[i], marker='.')
        plt.ylabel("CometKiwi")
        plt.xlabel("Metrical distance")

    if not plot_besides:
        plt.show()
    else:
        plt.subplot(1, 2, 2)

    # visualize rhyme scheme similarity
    for i in range(len(tags)):
        plt.scatter([x[2]+random.randrange(-10,10)/1000 for x in data[tags[i]]], [y[0] for y in data[tags[i]]], c=colors[i], marker='.')
        plt.ylabel("CometKiwi")
        plt.xlabel("Rhyme scheme similarity")
    plt.show()