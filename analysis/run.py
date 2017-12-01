# -*- coding: utf-8 -*-

import copy
import csv
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import vokativ

GENERATIONS = (
    ("Tichá genenerace", (1925, 1945)),
    ("Baby boomers", (1945, 1963)),
    ("Generace X", (1963, 1980)),
    ("Generace Y", (1980, 1998)),
    ("Generace Z", (2000, 2017))
)


def check_data_are_consistent(data):
    names_sum = sum(name_data["SUM"] for name_data in data["NAMES"].values())
    assert names_sum == data["SUM"]
    assert sum(data["YEAR_SUMS"]) == data["SUM"]


def convert_row_values(row):
    return tuple(int(value) for value in row)


def name_to_lower(name):
    return name[0] + name[1:].lower()


def configure_matplotlib():
    matplotlib.rc('font', family='DejaVu Sans')
    plt.style.use('fivethirtyeight')


def load_data():
    print("LOADING DATA...")
    reader = csv.reader(open('names.csv', 'r'), delimiter=',')
    data = {}
    data["NAMES"] = {}

    for row in reader:
        if row[0] == "JMÉNO":
            data["YEARS"] = tuple(row[1:-2])
        elif row[0] == "SOUČET":
            data["YEAR_SUMS"] = convert_row_values(row[1:-2])
            data["SUM"] = int(row[-1])
        else:
            data["NAMES"][row[0]] = {
                "FREQUENCIES": convert_row_values(row[1:-2]),
                "SUM": int(row[-1]),
                "SEX": vokativ.sex(row[0])
            }

    check_data_are_consistent(data)
    return data


def filter_years(data, year_from=0, year_to=9999):
    print("FILTERING YEARS...")
    data = copy.deepcopy(data)

    slice_from = year_from - int(data["YEARS"][0])
    slice_to = year_to - int(data["YEARS"][0])
    data["YEARS"] = data["YEARS"][slice_from:slice_to]
    data["YEAR_SUMS"] = data["YEAR_SUMS"][slice_from:slice_to]
    data["SUM"] = sum(data["YEAR_SUMS"])

    for name_data in data["NAMES"].values():
        name_data["FREQUENCIES"] = (
            name_data["FREQUENCIES"][slice_from:slice_to])
        name_data["SUM"] = sum(name_data["FREQUENCIES"])

    check_data_are_consistent(data)
    return data


def filter_years_and_recount(data, year_from, year_to):
    data_in_year_range = filter_years(data, year_from, year_to)
    add_normalized_frequencies(data_in_year_range)

    check_data_are_consistent(data)
    return data_in_year_range


def filter_sex_and_recount(old_data):
    print("FILTERING SEX...")
    data = copy.deepcopy(old_data)

    sex_names_data = {'m': {},
                      'w': {}}
    year_sums = {'m': tuple(0 for _ in range(len(data["YEAR_SUMS"]))),
                 'w': tuple(0 for _ in range(len(data["YEAR_SUMS"])))}
    for name, name_data in data["NAMES"].items():
        sex = name_data["SEX"]
        sex_names_data[sex][name] = name_data
        year_sums[sex] = tuple(
            name_data["FREQUENCIES"][i] + year_sums[sex][i]
            for i in range(len(year_sums[sex])))

    m_data = {
        "YEARS": data["YEARS"],
        "NAMES": sex_names_data['m'],
        "YEAR_SUMS": year_sums['m'],
        "SUM": sum(year_sums['m'])
    }
    w_data = {
        "YEARS": data["YEARS"],
        "NAMES": sex_names_data['w'],
        "YEAR_SUMS": year_sums['w'],
        "SUM": sum(year_sums['w'])
    }

    add_normalized_frequencies(m_data)
    add_normalized_frequencies(w_data)

    check_data_are_consistent(m_data)
    check_data_are_consistent(w_data)
    assert m_data["SUM"] + w_data["SUM"] == data["SUM"]
    return m_data, w_data


def merge_multinames(data):
    print("MERGING MULTINAMES...")
    names_data = data["NAMES"]

    base_name = ""
    base_name_data = {}
    merged_names_data = {}
    for name in sorted(names_data.keys()):
        if (name.split(' ')[0] == base_name or
                name.split('-')[0] == base_name):
            base_name_data["SUM"] += names_data[name]["SUM"]
            name_freqs = names_data[name]["FREQUENCIES"]
            base_name_data["FREQUENCIES"] = tuple(
                name_freqs[i] + base_name_data["FREQUENCIES"][i]
                for i in range(len(name_freqs)))
        else:
            if base_name:
                merged_names_data[base_name] = dict(base_name_data)
            base_name_data = names_data[name]
            base_name = name

    if base_name:
        merged_names_data[base_name] = dict(base_name_data)

    data["NAMES"] = merged_names_data
    check_data_are_consistent(data)


def filter_names(data):
    print("FILTERING NAMES...")
    data["NAMES"] = {
        name : name_data for name, name_data in
        data["NAMES"].items() if name_data["SUM"] > 0
    }

    year_sums = tuple(0 for _ in range(len(data["YEAR_SUMS"])))
    for name_data in data["NAMES"].values():
        year_sums = tuple(
            name_data["FREQUENCIES"][i] + year_sums[i]
            for i in range(len(year_sums)))

    data["YEAR_SUMS"] = year_sums
    data["SUM"] = sum(year_sums)

    check_data_are_consistent(data)


def add_normalized_frequencies(data):
    print("ADDING NORMALIZED FREQUENCIES...")
    year_sums = data["YEAR_SUMS"]

    for name_data in data["NAMES"].values():
        name_data["NORMALIZED_FREQUENCIES"] = tuple(
            name_data["FREQUENCIES"][i] / year_sums[i] for
            i in range(len(year_sums)))
        name_data["NORMALIZED_SUM"] = name_data["SUM"] / data["SUM"]


def show_names_graph(names_to_plot, data, title="", highlight_x=None):
    ax = plt.subplot()

    for name in names_to_plot:
        name_data = data["NAMES"][name]
        plt.plot(data["YEARS"], name_data["NORMALIZED_FREQUENCIES"],
                 label=name_to_lower(name), linewidth=2)

    plt.xlim(int(data["YEARS"][0]), int(data["YEARS"][-1]))
    plt.xticks(range(int(data["YEARS"][0]), int(data["YEARS"][-1]), 10))
    if highlight_x:
        plt.axvspan(highlight_x[0], highlight_x[1], color='grey', alpha=0.5)
    plt.xlabel("Rok")

    plt.ylim(0, 0.16)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
    plt.ylabel("Procento narozených")

    plt.title(title)
    plt.legend()

    plt.show()


def get_first_n_names_sorted(data, quantity, sort_key):
    sorted_names_data = sorted(
        data["NAMES"].items(), key=sort_key, reverse=True)[:quantity]
    return tuple(name for name, _ in sorted_names_data)

def graphs_for_generations(data, add_to_title):
    for generation_name, generation_range in GENERATIONS:
        data_in_year_range = filter_years_and_recount(
            data, year_from=generation_range[0],
            year_to=generation_range[1])
        names_to_plot = get_first_n_names_sorted(
            data_in_year_range, quantity=4,
            sort_key=lambda name_data: name_data[1]["SUM"])
        show_names_graph(
            names_to_plot, data, title=generation_name + " — " + add_to_title,
            highlight_x=generation_range)

def run():
    configure_matplotlib()

    data = load_data()
    data = filter_years(data, year_from=1925)
    merge_multinames(data)
    filter_names(data)

    data_man, data_woman = filter_sex_and_recount(data)
    graphs_for_generations(data_man, add_to_title="Muži")
    graphs_for_generations(data_woman, add_to_title="Ženy")
    names_to_plot = get_first_n_names_sorted(
        data_man, quantity=5, sort_key=lambda name_data: name_data[1]["SUM"])
    #show_names_graph(names_to_plot, data_man)
    names_to_plot = get_first_n_names_sorted(
        data, quantity=10,
        sort_key=lambda name_data: max(name_data[1]["NORMALIZED_FREQUENCIES"]))
    #show_names_graph(names_to_plot, data)

if __name__ == "__main__":
    run()
