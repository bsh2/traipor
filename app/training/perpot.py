from __future__ import division


def make_load_func(plan):

    def getload(t):
        return plan[t]

    return getload


def calc_strainrate(strainpot, perfpot, straindelay):
    return min(min(1, strainpot), max(0, perfpot)) / straindelay


def calc_responserate(responsepot, perfpot, responsedelay):
    return min(min(1, responsepot), min(1, 1 - perfpot)) / responsedelay


def calc_overflowrate(strainpot, overflowdelay):
    return max(0, strainpot - 1) / overflowdelay


def performance_over_time(plan,
                          strainpot,
                          responsepot,
                          perfpot,
                          straindelay,
                          responsedelay,
                          overflowdelay):
    loadrate = make_load_func(plan)
    n = len(plan)
    perfpots = [0.0] * n

    for day in range(n):
        strainpot += loadrate(day)
        responsepot += loadrate(day)

        strainrate = calc_strainrate(strainpot, perfpot, straindelay)
        responserate = calc_responserate(responsepot, perfpot, responsedelay)
        if overflowdelay != 0:
            overflowrate = calc_overflowrate(strainpot, overflowdelay)
        else:
            overflowrate = 0

        strainpot = strainpot - strainrate - overflowrate
        responsepot = responsepot - responserate
        perfpot = perfpot + responserate - strainrate - overflowrate
        perfpots[day] = perfpot

    return perfpots


def performance_over_time2(plan, parms):
    return performance_over_time(plan,
                                 parms[0],
                                 parms[1],
                                 parms[2],
                                 parms[3],
                                 parms[4],
                                 parms[5])


def leistungs_entwicklung(n,
                          strainpot,
                          responsepot,
                          perfpot,
                          straindelay,
                          responsedelay,
                          overflowdelay,
                          loadrate):
    perfpots = [0.0] * n

    for day in range(n):
        strainpot += loadrate(day)
        responsepot += loadrate(day)

        strainrate = calc_strainrate(strainpot, perfpot, straindelay)
        responserate = calc_responserate(responsepot, perfpot, responsedelay)
        if overflowdelay != 0:
            overflowrate = calc_overflowrate(strainpot, overflowdelay)
        else:
            overflowrate = 0

        strainpot = strainpot - strainrate - overflowrate
        responsepot -= responserate
        perfpot = perfpot + responserate - strainrate - overflowrate
        perfpots[day] = perfpot

    return perfpots


def after_plan(plan, **kwargs):
    e = performance_over_time(plan,
                              kwargs['strainpot'],
                              kwargs['responsepot'],
                              kwargs['perfpot'],
                              kwargs['straindelay'],
                              kwargs['responsedelay'],
                              kwargs['overflowdelay'])
    return e[-1]


def calc_pp_load_scale_factor(values):
    '''calculate the PerPot scale factor for load values'''
    return 1 / (max(values) * 1.25)


def calc_pp_perf_scale_factor(values):
    '''calculate the PerPot scale factor for performance values. allow an
    improvement of 50% before reaching the maximum of the normalization'''
    return 1 / (max(values) * 1.5)


def example_brueckner1():
    ''' shows super compensation and adaptation after some days of decrease
        under constant load
    '''
    # perpot model parameters
    straindelay = 3.0  # Verzoegerung Abbau BP
    responsedelay = 6  # Verzoegerung Abbau EP
    overflowdelay = 1.5  # Verzoegerung des Ueberlaufs des BP
    perfpot = 0.2
    responsepot = 0.0
    strainpot = 0.0
    kwargs = {'strainpot': strainpot,
              'responsepot': responsepot,
              'perfpot': perfpot,
              'straindelay': straindelay,
              'responsedelay': responsedelay,
              'overflowdelay': overflowdelay}
    print(kwargs)

    plan = [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1,
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    loadrate = make_load_func(plan)
    e = leistungs_entwicklung(len(plan),
                              kwargs['strainpot'],
                              kwargs['responsepot'],
                              kwargs['perfpot'],
                              kwargs['straindelay'],
                              kwargs['responsedelay'],
                              kwargs['overflowdelay'],
                              loadrate)
    for v in e:
        print(v)


def example_brueckner2():
    ''' there's no super compensation after a single training
    '''
    # perpot model parameters
    straindelay = 3.0  # Verzoegerung Abbau BP
    responsedelay = 6  # Verzoegerung Abbau EP
    overflowdelay = 1.5  # Verzoegerung des Ueberlaufs des BP
    perfpot = 0.2
    responsepot = 0.0
    strainpot = 0.0
    kwargs = {'strainpot': strainpot,
              'responsepot': responsepot,
              'perfpot': perfpot,
              'straindelay': straindelay,
              'responsedelay': responsedelay,
              'overflowdelay': overflowdelay}
    print(kwargs)

    plan = [0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    loadrate = make_load_func(plan)
    e = leistungs_entwicklung(len(plan),
                              kwargs['strainpot'],
                              kwargs['responsepot'],
                              kwargs['perfpot'],
                              kwargs['straindelay'],
                              kwargs['responsedelay'],
                              kwargs['overflowdelay'],
                              loadrate)
    for v in e:
        print(v)


def example_bigloadproblem():
    ''' with a big enough load the model shows an immediate increase of
        performance without first going down'''
    # perpot model parameters
    straindelay = 3.0  # Verzoegerung Abbau BP
    responsedelay = 6  # Verzoegerung Abbau EP
    overflowdelay = 1.5  # Verzoegerung des Ueberlaufs des BP
    perfpot = 0.2
    responsepot = 0.0
    strainpot = 0.0
    kwargs = {'strainpot': strainpot,
              'responsepot': responsepot,
              'perfpot': perfpot,
              'straindelay': straindelay,
              'responsedelay': responsedelay,
              'overflowdelay': overflowdelay}
    print(kwargs)

    plan = [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    loadrate = make_load_func(plan)
    e = leistungs_entwicklung(len(plan),
                              kwargs['strainpot'],
                              kwargs['responsepot'],
                              kwargs['perfpot'],
                              kwargs['straindelay'],
                              kwargs['responsedelay'],
                              kwargs['overflowdelay'],
                              loadrate)
    for v in e:
        print(v)


if __name__ == '__main__':
    # example_brueckner1()
    # example_brueckner2()
    example_bigloadproblem()
