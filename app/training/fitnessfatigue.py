from __future__ import division
import numpy as np


def make_load_func(plan):

    def getload(t):
        return plan[t-1]  # ff model plans start with index 1

    return getload


def g(t, tau_1, w):
    '''time continuous version of g'''
    return w(t) * np.exp(-t/tau_1)


def discrete_g(n, tau_1, w):
    g_values = np.empty(n - 1, dtype=np.double)
    for i in range(1, n):
        g_values[i-1] = w(i) * np.exp(-(n-i)/tau_1)
    return np.sum(g_values)


def h(t, tau_2, w):
    '''time continuous version of h'''
    return w(t) * np.exp(-t/tau_2)


def discrete_h(n, tau_2, w):
    h_values = np.empty(n - 1, dtype=np.double)
    for i in range(1, n):
        h_values[i-1] = w(i) * np.exp(-(n-i)/tau_2)
    return np.sum(h_values)


def p(t, initial_p, tau_1, tau_2, k_1, k_2, w):
    '''time continuous performance output'''
    return initial_p + k_1 * g(t, tau_1, w) - k_2 * h(t, tau_2, w)


def discrete_p(n, initial_p, tau_1, tau_2, k_1, k_2, w):
    g = discrete_g(n, tau_1, w)
    h = discrete_h(n, tau_2, w)
    return initial_p + k_1 * g - k_2 * h


def discrete_p_curve_fit(plans, initial_p, k_1, tau_1, k_2, tau_2):
    '''takes a list of plans. to be used with scipy.optimize.curve_fit'''
    results = [0.0] * len(plans)
    for i, plan in enumerate(plans):
        w = make_load_func(plan)
        n = len(plan)
        g = discrete_g(n, tau_1, w)
        h = discrete_h(n, tau_2, w)
        results[i] = initial_p + k_1 * g - k_2 * h
    return results


def leistungs_entwicklung(n, initial_p, tau_1, tau_2, k_1, k_2, w):
    p = []
    for i in range(1, n+1):
        g = discrete_g(i, tau_1, w)
        h = discrete_h(i, tau_2, w)
        p.append(initial_p + k_1 * g - k_2 * h)
    return p


def performance_over_time(plan, initial_p, k_1, tau_1, k_2, tau_2):
    n = len(plan)
    p_values = np.empty(n, dtype=np.double)
    w = make_load_func(plan)
    for i in range(1, n+1):
        g = discrete_g(i, tau_1, w)
        h = discrete_h(i, tau_2, w)
        p_values[i-1] = (initial_p + k_1 * g - k_2 * h)
    return p_values


def performance_over_time2(plan, parms):
    return performance_over_time(plan,
                                 parms[0],
                                 parms[1],
                                 parms[2],
                                 parms[3],
                                 parms[4])


def after_plan(plan, **kwargs):
    w = make_load_func(plan)
    return discrete_p(len(plan),
                      kwargs['initial_p'],
                      kwargs['tau_1'],
                      kwargs['tau_2'],
                      kwargs['k_1'],
                      kwargs['k_2'],
                      w)


def examplenew():
    plan1 = [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1,
             0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
             0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
             0.1, 0.1, 0.1, 0.1, 0.1, 0.9, 0.0]
    initial_p = 0.2
    tau_1 = 10
    tau_2 = 6
    k_1 = 0.15
    k_2 = 0.13
    e = performance_over_time(plan1, initial_p, tau_1, tau_2, k_1, k_2)
    for v in e:
        print(v)


def example():
    plan1 = [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1,
             0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
             0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
             0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    plan2 = [0.9, 0.9, 0.9, 0.0, 0.9, 0.9, 0.0,
             0.9, 0.9, 0.9, 0.0, 0.9, 0.9, 0.0,
             0.9, 0.9, 0.9, 0.0, 0.9, 0.9, 0.0,
             0.9, 0.9, 0.9, 0.0, 0.9, 0.9, 0.0]
    plan3 = [0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    w = make_load_func(plan3)
    n = len(plan3)
    initial_p = 0.2
    tau_1 = 10
    tau_2 = 6
    k_1 = 0.15
    k_2 = 0.13
    e = leistungs_entwicklung(n, initial_p, tau_1, tau_2, k_1, k_2, w)
    for v in e:
        print(v)


def example2():
    plan = [0.05, 0.05, 0.05, 0.0, 0.05, 0.05, 0.0,
            0.05, 0.05, 0.05, 0.0, 0.05, 0.00, 0.0]
    w = make_load_func(plan)
    n = len(plan)
    initial_p = 0.1
    k_1 = 0.242
    tau_1 = 45.2
    k_2 = 0.372
    tau_2 = 11.3

    e = leistungs_entwicklung(n, initial_p, tau_1, tau_2, k_1, k_2, w)
    for v in e:
        print(v)


if __name__ == '__main__':
    examplenew()
