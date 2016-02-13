from enum import Enum, unique
from itertools import islice, takewhile
from math import sqrt
from datetime import date, datetime, timedelta

WORKLOAD_FACTOR = 0.001


@unique
class WeekDays(Enum):
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6

    @classmethod
    def to_short_str(cls, day):
        shorts = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        return shorts[day]


def microcycle_days(weekly_training_days, weeks):
    """generates indexes of training days during the weeks"""
    training_day_indexes = []
    for w in range(weeks):
        for d in weekly_training_days:
            training_day_indexes.append(w * 7 + d.value)
    return training_day_indexes


def filter_days(training_days, off_days):
    """returns indexes of training_days with off_days filtered out"""
    training_days = list(filter(lambda t: t not in off_days, training_days))
    return training_days


def filter_weeks(training_days, off_weeks):
    """returns indexes of training_days with off_weeks filtered out"""
    off_days = []
    for w in off_weeks:
        off_days.extend(list(range(w * 7, (w + 1) * 7)))
    return filter_days(training_days, off_days)


def calc_offdays(training_days, weeks):
    """returns indexes of off-days during the weeks"""
    all_plan_days = set(list(range(7 * weeks)))
    return all_plan_days - set(training_days)


def fitness(plan, goal, threshold, model_perf_func, **model_parameters):
    """returns tuple of
    - a fitness score which takes the total workload into account
    - a boolean indicating if the solution approximation deviation is <= the
    given threshold
    """
    plan_perf = model_perf_func(plan, **model_parameters)
    total_workload = sum(plan)
    fitness_wo_load = 1 - (abs(goal - plan_perf))
    fitness_with_load = fitness_wo_load - WORKLOAD_FACTOR * total_workload
    approx_deviation = abs(100 - (plan_perf / goal) * 100)
    se_threshold = approx_deviation <= threshold
    return fitness_with_load, se_threshold


def approximation_quality(plan_perf, goal):
    if plan_perf < goal:
        return (plan_perf / goal) * 100
    else:
        return (goal / plan_perf) * 100


def print_enumerated_list(l):
    for i, v in enumerate(l):
        print('{} {}'.format(i, v))


def print_ea_result(solution, solution_fitness, p_after_plan, goal):
    print_enumerated_list(solution)
    print('ea solution fitness: {}'.format(solution_fitness))
    print('after plan: {}, {:.8}% of goal {}'.format(p_after_plan,
                                                     p_after_plan / goal * 100,
                                                     goal))


def sort_microcycles_asc(plan):
    """sort successive training days in a plan in a ascending way"""
    return sort_microcycles(plan)


def sort_microcycles_dsc(plan):
    """sort successive training days in a plan in a descending way"""
    return sort_microcycles(plan, True)


def sort_microcycles(plan, descending=False):
    """sort successive training days in a plan, either ascending or descending
    """
    if len(plan) <= 1:
        return plan
    if plan[0] == 0.0:
        return [plan[0]] + sort_microcycles(list(islice(plan, 1, None)),
                                            descending)
    else:
        cycle = list(takewhile(lambda x: x > 0.0, plan))
        cycle.sort(reverse=descending)
        plan = list(islice(plan, len(cycle), None))
        return cycle + sort_microcycles(plan, descending)


def sort_loads(plan):
    """sort loads in plan while keeping the positions of the loaded days"""
    loads = []
    loaded_days = []
    for index, load in enumerate(plan):
        if load > 0.0:
            loaded_days.append(index)
            loads.append(load)
    loads = sorted(loads)
    for i in loaded_days:
        plan[i] = loads.pop(0)
    return plan


def sort_microcycles_asc_with_tamper_week(plan):
    """sort loads in plan ascending but make the last week a tamper phase"""
    return sort_microcycles_with_tamper_week(plan)


def sort_microcycles_dsc_with_tamper_week(plan):
    """sort loads in plan descending but make the last week a tamper phase"""
    return sort_microcycles_with_tamper_week(plan, True)


def sort_microcycles_with_tamper_week(plan, descending=False):
    """sort loads in plan but make the last week a tamper phase"""
    plan = sort_loads(plan)
    if descending:
        plan = sort_microcycles(plan, descending)
    weeks = int(len(plan) / 7)
    if weeks >= 2:
        plan = swap_weeks(plan, weeks - 2, weeks - 1)
    return plan


def swap_weeks(plan, i, j):
    for d in range(7):
        plan[i * 7 + d], plan[j * 7 + d] = plan[j * 7 + d], plan[i * 7 + d]
    return plan


def acc_small_loads(plan, threshold_fac=0.1, max_load=None):
    """returns a new plan in which the sum of small loads in a week are added to
    the smallest load which is above the threshold. The small loads are replaced
    with 0.0. Small loads are loads < threshold_fac * max(plan)
    """
    plan_new = []
    load_threshold = max(plan) * threshold_fac
    weeks = int(len(plan) / 7)
    for i in range(weeks):
        week = plan[i*7:(i+1)*7]
        small_loads = sum(filter(lambda l: l < load_threshold, week))
        if small_loads == 0.0:  # nothing below threshold or off-week
            plan_new += week
            continue
        week_new = [0.0 if l < load_threshold else l for l in week]
        if week_new.count(0.0) != 7:    # not every load below threshold
            min_load = min(filter(lambda l: l > 0.0, week_new))
            idx = week_new.index(min_load)
        else:   # no off-week but all loads below load_threshold
            for j, l in enumerate(week):
                if l > 0.0:
                    idx = j
                    break
        week_new[idx] += small_loads
        if max_load is not None and week_new[idx] > max_load:
            week_new[idx] = max_load
        plan_new += week_new
    return plan_new


def parse_comma_separated_ints(field_string):
    '''returns a list of ints for a string like "1, 2, 3"'''
    if len(field_string) > 0:
        return list(map(int, field_string.split(',')))
    else:
        return []


def parse_comma_separated_dates(string):
    '''takes a string of comma separated yyyy-mm-dd dates and returns a list of
    date objects'''
    if len(string) == 0:
        return []
    dates = string.split(',')
    return list(map(lambda x: datetime.strptime(x, '%Y-%m-%d').date(), dates))


def dates_to_indexes(start_date, dates, weeks):
    '''transforms the given dates to index values with respect to start_date.
    dates before start_date and after start_date + weeks are ignored'''
    indexes = []
    end_date = start_date + timedelta(days=(weeks * 7 - 1))
    for d in dates:
        if start_date <= d <= end_date:
            indexes.append((d - start_date).days)
    return indexes


def next_monday(excluding_today):
    '''returns date of next monday'''
    delta1 = timedelta(days=1)
    d = date.today()
    if excluding_today:
        d += delta1
    while d.weekday() != 0:
        d += delta1
    return d


def next_monday_after(day):
    '''returns date of next monday after given day'''
    exclude_today = day == date.today()
    return next_monday(exclude_today)


def days_between_last_training_and_next_monday(last_training):
    '''returns count of full days between last_training and next monday'''
    assert((date.today() - last_training).days >= 0)
    nxt_mday = next_monday_after(last_training)
    print('nxt_mday = {}'.format(nxt_mday))
    return (nxt_mday - last_training).days - 1


def diffs_stats(pairs):
    """returns the avg and the maximum difference between the given pairs and
    the count of cases where the first element is bigger than the second
    """
    s = 0.0
    m = 0.0
    n = 0
    for (old, new) in pairs:
        d = new - old   # not using abs here on purpose
        s += d
        if new < old:
            n += 1
        if abs(d) > abs(m):
            m = d
    return s / len(pairs), m, n


def standard_deviation_of_diffs(pairs):
    n = len(pairs)
    diffs = []
    var = 0.0
    for (i, j) in pairs:
        diffs.append(abs(i - j))
    mu = sum(diffs) / n
    for x in diffs:
        var += (x - mu)**2 / n
    return sqrt(var)
