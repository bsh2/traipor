import csv
from datetime import date, datetime
from itertools import chain, groupby
import numpy as np
from re import fullmatch
import re
import sys


def calc_rmse(real_values, model_values):
    '''returns the root-mean-square error'''
    return np.sqrt(np.mean(np.square(np.subtract(real_values, model_values))))


def calc_error_squares(real_values, model_values):
    '''returns a list of error squares'''
    return np.square(np.subtract(real_values, model_values))


def calc_residuals(model_vals, real_vals):
    '''returns the list of residuals'''
    return model_vals - real_vals


def csv_value_dict_from_iter(f, must_have_metrics=None):
    '''construct a dictionary from the given iterator f. the fieldnames are the
    keys, the columns are the values. optionally filter out rows with certain
    0.0 values'''
    dictreader = csv.DictReader(f)
    return build_csv_value_dict(dictreader, must_have_metrics)


def csv_value_dict_from_path(path, must_have_metrics=None, drop_history=False):
    '''construct a dictionary from a csv file. the fieldnames are the keys, the
    columns are the values. optionally filter out rows with certain 0.0 values
    '''
    try:
        with open(path) as f:
            lines = f.read().splitlines()
            if drop_history:
                lines = drop_before_last_year(lines)
            return csv_value_dict_from_iter(lines, must_have_metrics)
    except UnicodeError:
        pass
    try:
        with open(path, encoding='latin_1') as f:
            lines = f.read().splitlines()
            if drop_history:
                lines = drop_before_last_year(lines)
            return csv_value_dict_from_iter(lines, must_have_metrics)
    except UnicodeError:
        pass
    with open(path, encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
        if drop_history:
            lines = drop_before_last_year(lines)
        return csv_value_dict_from_iter(lines, must_have_metrics)


def csv_value_dict_from_pathold(path, must_have_metrics=None):
    '''construct a dictionary from a csv file. the fieldnames are the keys, the
    columns are the values. optionally filter out rows with certain 0.0 values
    '''
    try:
        with open(path) as f:
            dictreader = csv.DictReader(f)
            return build_csv_value_dict(dictreader, must_have_metrics)
    except UnicodeError:
        pass
    try:
        with open(path, encoding='latin_1') as f:
            dictreader = csv.DictReader(f)
            return build_csv_value_dict(dictreader, must_have_metrics)
    except UnicodeError:
        pass
    with open(path, encoding='utf-8', errors='ignore') as f:
            dictreader = csv.DictReader(f)
            return build_csv_value_dict(dictreader, must_have_metrics)


def build_csv_value_dict(dictreader, must_have_metrics=None):
    '''construct a dictionary from the given dictreader. the fieldnames are the
    keys, the columns are the values. optionally filter out rows with certain
    0.0 values'''
    csvdic = {}
    # set up keys
    for name in dictreader.fieldnames:
        norm_name = name.strip()
        if norm_name != '':
            csvdic[norm_name] = []
    # fill csvdic with row values if ok
    for row_dic in dictreader:
        norm_row_dic = normalize_dic_keys(row_dic)
        if must_have_metrics is not None and \
           not row_has_must_have_metrics(norm_row_dic, must_have_metrics):
            continue
        for name in dictreader.fieldnames:
            norm_name = name.strip()
            if name.strip() != '':
                csvdic[norm_name].append(norm_row_dic[norm_name])
    return csvdic


def drop_before_last_year(csv_lines):
    '''returns the given csv lines with entries before last year dropped'''
    last_year = str(datetime.now().year - 1)[3:]
    this_year = str(datetime.now().year)[3:]

    if re.fullmatch('^[1]?[0-9]/[123]?[0-9]/\d\d\d\d.*', csv_lines[1]):
        p = '^[1]?[0-9]/[123]?[0-9]/\d\d\d[{}|{}].*'.format(last_year,
                                                            this_year)
    else:
        p = '^[01][0-9]/[0-3][0-9]/1[{}|{}].*'.format(last_year, this_year)

    cp = re.compile(p)
    idx = 0
    for i, l in enumerate(csv_lines):
        if cp.fullmatch(l):
            idx = i
            break
    return [csv_lines[0]] + csv_lines[idx:]


def drop_before_this_year(csv_lines):
    '''returns the given csv lines with entries before this year dropped'''
    this_year = str(datetime.now().year)[3:]

    if re.fullmatch('^[1]?[0-9]/[123]?[0-9]/\d\d\d\d.*', csv_lines[1]):
        p = '^[1]?[0-9]/[123]?[0-9]/\d\d\d{}.*'.format(this_year)
    else:
        p = '^[01][0-9]/[0-3][0-9]/1{}.*'.format(this_year)

    cp = re.compile(p)
    idx = 0
    for i, l in enumerate(csv_lines):
        if cp.fullmatch(l):
            idx = i
            break
    return [csv_lines[0]] + csv_lines[idx:]


def row_has_must_have_metrics(row_dictionary, metrics):
    '''returns True if given metrics in row_dictionary contain at least one
    value > 0.0 and all values are not inf, else False
    '''
    try:
        vals = [float(row_dictionary[m]) for m in metrics]
        no_infs = not any([np.isinf(v) for v in vals])
        at_least_one_value = any([v > 0.0 for v in vals])
        return no_infs and at_least_one_value
    except:
        print("row_has_must_have_metrics(): ", sys.exc_info()[0])
        raise


def normalize_dic_keys(row_dic):
    '''returns a normalized (stripped, non-empty key names) copy of the given
    dict'''
    normed_dic = dict()
    for k in row_dic.keys():
        norm_k = k.strip()
        if norm_k != '':
            normed_dic[norm_k] = row_dic[k]
    return normed_dic


def choose_best_perfs_per_day(csvdic, perf_metric):
    '''choose the best performance metric per day if there's more than one.
    returns a list of perf_metric values.'''
    dates = parse_date_field(csvdic['date'])
    perfs = list(map(float, csvdic[perf_metric]))
    unique_dates = []
    date_groups = []
    for k, g in groupby(zip(dates, perfs), lambda x: x[0]):
        unique_dates.append(k)
        date_groups.append(list(g))
    best_perfs_per_day = []
    for date_group in date_groups:
        best_perfs_per_day.append(max([p[1] for p in date_group]))
    return best_perfs_per_day


def span_best_over_days(csvdic, load_metric, perf_metric):
    '''choose the best performance value per day and span it over all
    training sessions of the day. returns the list of training dates, the list
    of spanned performance values and a list of loads.'''
    def key_func(x):
        return x[0].year, x[0].month, x[0].day  # group by key (year, month, day)

    dates = parse_date_field(csvdic['date'])
    loads = list(map(float, csvdic[load_metric]))
    perfs = list(map(float, csvdic[perf_metric]))
    trainings = zip(dates, loads, perfs)
    return span_best_over_time_frame(trainings, key_func)


def span_best_over_weeks(csvdic, load_metric, perf_metric):
    '''choose the best performance value per week and span it over all
    training sessions of the week. returns the list of training dates, the list
    of spanned performance values and a list of loads.'''
    def key_func(x):
        d = date.isocalendar(x[0])
        return d[0], d[1]

    dates = parse_date_field(csvdic['date'])
    loads = list(map(float, csvdic[load_metric]))
    perfs = list(map(float, csvdic[perf_metric]))
    trainings = zip(dates, loads, perfs)
    return span_best_over_time_frame(trainings, key_func)


def span_best_over_months(csvdic, load_metric, perf_metric):
    '''choose the best performance value per month and span it over all
    training sessions of the month. returns the list of training dates, the list
    of spanned performance values and a list of loads.'''
    def key_func(x):
        return x[0].year, x[0].month  # group by key (year, month)

    dates = parse_date_field(csvdic['date'])
    loads = list(map(float, csvdic[load_metric]))
    perfs = list(map(float, csvdic[perf_metric]))
    trainings = zip(dates, loads, perfs)
    return span_best_over_time_frame(trainings, key_func, min_group_size=4)


def span_best_over_time_frame(date_load_perf_tuples,
                              key_func,
                              min_group_size=1):
    '''choose the best performance value per grouped time frame and span it over
    all training sessions of the time frame. returns the list of training dates,
    the list of spanned performance values and a list of loads.'''
    unique_time_frames = []
    time_frame_groups = []
    for k, g in groupby(date_load_perf_tuples, key_func):
        unique_time_frames.append(k)
        time_frame_groups.append(list(g))
    frame_dates = []
    frame_loads = []
    frame_perfs = []
    for group in time_frame_groups:
        # start with a group with enough data
        if frame_dates == []:
            t = [p[2] for p in group if p[2] > 0 and not np.isinf(p[2])]
            if len(t) < min_group_size:
                continue
        best = max([p[2] for p in group])
        # span over frame group only if perf value in frame data
        if best > 0 and not np.isinf(best):
            frame_dates += [p[0] for p in group]
            frame_loads += [p[1] for p in group]
            frame_perfs += [best] * len(group)
    assert(len(frame_dates) == len(frame_perfs))
    assert(len(frame_loads) == len(frame_perfs))
    return frame_dates, frame_loads, frame_perfs


def parse_date_field(dates):
    '''transforms a list of M/D/YYYY or MM/DD/YYYY strings into a list of date
    objects'''
    try:
        m = fullmatch('[1]?[0-9]/[123]?[0-9]/\d\d\d\d', dates[0])
        prep_dates = []
        if m is not None:
            for ds in dates:
                d, m, y = ds.split('/')
                prep_date = '{}/{}/{}'.format(d.zfill(2), m.zfill(2), y[2:4])
                prep_dates.append(prep_date)
        else:
            prep_dates = dates
        return list(map(lambda x: datetime.strptime(x, '%m/%d/%y').date(),
                        prep_dates))
    except:
        print("parse_date_field(): ", sys.exc_info()[0])
        raise


def date_load_tuples_2_plan(date_load_tuples):
    '''returns a list of loads. the days between training loads are filled with
    0.0 loads.'''
    n = len(date_load_tuples)
    if n == 0:
        return []
    plan = []
    plan.append(date_load_tuples[0][1])
    if n == 1:
        return plan
    for i in range(1, len(date_load_tuples)):
        delta = date_load_tuples[i][0] - date_load_tuples[i-1][0]
        for days in range(0, delta.days - 1):
            plan.append(0.0)    # TODO optimize
        plan.append(date_load_tuples[i][1])
    return plan


def date_value_tuples_2_calendar(date_value_tuples):
    '''returns a list of values. the days between values are filled with
    0.0 values.'''
    n = len(date_value_tuples)
    if n == 0:
        return []
    values = []
    values.append(date_value_tuples[0][1])
    if n == 1:
        return values
    for i in range(1, len(date_value_tuples)):
        delta = date_value_tuples[i][0] - date_value_tuples[i-1][0]
        for days in range(0, delta.days - 1):
            values.append(0.0)    # TODO optimize
        values.append(date_value_tuples[i][1])
    return values


def collapse_perfs_per_day(dates, perfs):
    '''choose only the best performance value per day. returns a list of
    (date, performance) tuples'''
    assert(len(dates) == len(perfs))
    date_groups = []
    unique_dates = []
    for k, g in groupby(zip(dates, perfs), lambda x: x[0]):
        date_groups.append(list(g))
        unique_dates.append(k)
    collapsed_perfs = []
    for date_group in date_groups:
        perfs_of_day = [x[1] for x in date_group]
        collapsed_perfs += [max(perfs_of_day)]
    return list(zip(unique_dates, collapsed_perfs))


def accumulate_loads_per_day(dates, loads):
    '''sum up the loads if there are more than one on a single day.
    returns a list of (date, load) tuples'''
    date_groups = []
    unique_dates = []
    for k, g in groupby(zip(dates, loads), lambda x: x[0]):
        date_groups.append(list(g))
        unique_dates.append(k)
    accumulated_loads = []
    for date_group in date_groups:
        load_sum = 0.0
        for l in date_group:
            load_sum += l[1]
        accumulated_loads.append(load_sum)
    return list(zip(unique_dates, accumulated_loads))


def plan_perfs_from_dic(csvdic,
                        load_metric,
                        perf_metric,
                        weekly_limit,
                        part_of_metrics=1.0):
    '''returns a tuple of lists. the first element is the plan containing the
    load_metric values. the second element are the performance metric values,
    here the best performance of a week or month is chosen and used for all
    training sessions of that time frame. the performance list is filled up with
    0.0 values on unmeasured days.  with part_of_metrics it's possible to limit
    how much is returned from the content of csvdic.'''
    if weekly_limit:
        dates, loads, perfs = span_best_over_weeks(csvdic,
                                                   load_metric,
                                                   perf_metric)
    else:
        dates, loads, perfs = span_best_over_months(csvdic,
                                                    load_metric,
                                                    perf_metric)
    # dates, loads, perfs = span_best_over_days(csvdic, load_metric, perf_metric)
    # deal with multiple training sessions per day
    date_load_tuples = accumulate_loads_per_day(dates, loads)
    date_perf_tuples = collapse_perfs_per_day(dates, perfs)
    n = int(len(date_load_tuples) * part_of_metrics)
    m = int(len(date_perf_tuples) * part_of_metrics)
    assert(n == m)
    plan = date_load_tuples_2_plan(date_load_tuples[0:n])
    perfs = date_value_tuples_2_calendar(date_perf_tuples[0:m])
    plan2 = date_load_tuples_2_plan(date_load_tuples[n:])
    perfs2 = date_value_tuples_2_calendar(date_perf_tuples[m:])
    assert(len(plan2) == len(perfs2))
    return plan, perfs, plan2, perfs2


def plan_perfs_from_dic2(csvdic,
                         load_metric,
                         perf_metric,
                         weekly_limit,
                         months_to_cut):
    '''returns a tuple of lists. the first element is the plan containing the
    load_metric values. the second element are the performance metric values,
    here the best performance of a week or month is chosen and used for all
    training sessions of that time frame. the performance list is filled up with
    0.0 values on unmeasured days.  with part_of_metrics it's possible to limit
    how much is returned from the content of csvdic.'''
    if weekly_limit:
        dates, loads, perfs = span_best_over_weeks(csvdic,
                                                   load_metric,
                                                   perf_metric)
    else:
        dates, loads, perfs = span_best_over_months(csvdic,
                                                    load_metric,
                                                    perf_metric)
    # dates, loads, perfs = span_best_over_days(csvdic, load_metric, perf_metric)
    # deal with multiple training sessions per day
    date_load_tuples = accumulate_loads_per_day(dates, loads)
    date_perf_tuples = collapse_perfs_per_day(dates, perfs)
    assert(len(date_load_tuples) == len(date_perf_tuples))
    n = find_index_to_cut_by_months([d[0] for d in date_load_tuples],
                                    months_to_cut)
    plan = date_load_tuples_2_plan(date_load_tuples[0:n])
    perfs = date_value_tuples_2_calendar(date_perf_tuples[0:n])
    plan2 = date_load_tuples_2_plan(date_load_tuples[n:])
    perfs2 = date_value_tuples_2_calendar(date_perf_tuples[n:])
    assert(len(plan2) == len(perfs2))
    return plan, perfs, plan2, perfs2


def find_index_to_cut_by_months(dates, months_to_cut):
    def key_func(x):
        return x.year, x.month  # group by key (year, month)

    if months_to_cut < 1:
        return len(dates)
    unique_time_frames = []
    groups = []
    for k, g in groupby(dates, key_func):
        unique_time_frames.append(k)
        groups.append(list(g))
    second_half_length = len(list(chain.from_iterable(groups[-months_to_cut:])))
    first_half_length = len(dates) - second_half_length
    return first_half_length


def measurement_indexes(values):
    '''returns a list of indexes in the given values where a value is > 0.0'''
    return [i for i, v in enumerate(values) if v > 0.0]


def filter_model_perf_values_2_load_days(plan, model_perf_values):
    '''filters model_perf_values to only contain values which correspond to
    training days in the plan'''
    load_indexes = measurement_indexes(plan)
    return [v for i, v in enumerate(model_perf_values) if i in load_indexes]


def filter_model_perfs_2_real_perfs(model_perfs, real_perfs):
    load_indexes = measurement_indexes(real_perfs)
    return [v for i, v in enumerate(model_perfs) if i in load_indexes]


def choose_init_p(plan, perfs):
    '''heuristic to choose an init_p. returns the chosen init_p and all the
    loads since then leading to the current performance. can be used for Fitness
    Fatigue and PerPot.'''
    initial_p = min(filter(lambda x: x > 0, perfs))
    r_index = perfs[::-1].index(initial_p)  # right most index of initial_p
    initial_p_index = len(perfs) - 1 - r_index
    print('initial_p_index {} in {} days'.format(initial_p_index, len(perfs)))
    plan_since_initial_p = plan[initial_p_index:]
    perfs_since_initial_p = perfs[initial_p_index:]
    assert(len(plan_since_initial_p) == len(perfs_since_initial_p))
    return initial_p, plan_since_initial_p, perfs_since_initial_p


def fillup_perf_list_to_plan(perfs, plan):
    '''returns the given list of perf values filled up with 0.0 values on
    off days of the given plan'''
    filled_perfs = []
    perfs_index = 0
    for l in plan:
        if l > 0.0:
            filled_perfs.append(perfs[perfs_index])
            perfs_index += 1
        else:
            filled_perfs.append(0.0)
    assert(len(filled_perfs) == len(plan))
    return filled_perfs
