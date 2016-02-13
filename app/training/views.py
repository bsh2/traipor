import sys
from flask import Markup, flash, redirect, url_for, render_template, request
from flask.ext.login import login_required, current_user
from . import training
from ..models import FFPlan, PPPlan, JobType, PLANS_LIMIT
from .. import db
from .tasks import PlanRequest
from .tasks import ff_fitting_task, ff_genplan_task, ff_genplan_cmaes_task
from .tasks import pp_fitting_task, pp_genplan_task, pp_genplan_cmaes_task
from .forms import StartFittingForm, GeneratePlanForm
from .forms import DeletePlanForm, ShowPlanForm
from .plan_util import WeekDays, parse_comma_separated_ints
from .plan_util import parse_comma_separated_dates, dates_to_indexes
from .plan_util import next_monday_after


metric_blacklist = ['date', 'time', 'filename']


@training.route('/ff_fitting', methods=['GET', 'POST'])
@login_required
def ff_fitting():
    return handle_fitting_request(JobType.ff_fitting,
                                  ff_fitting_task,
                                  'Fitness Fatigue')


@training.route('/pp_fitting', methods=['GET', 'POST'])
@login_required
def pp_fitting():
    return handle_fitting_request(JobType.pp_fitting,
                                  pp_fitting_task,
                                  'PerPot')


def handle_fitting_request(jobtype, fitting_task, model_name):
    form = StartFittingForm()
    mf = current_user.gc_metrics_file.first()
    if mf is None:
        flash('First upload your GoldenCheetah metrics file.')
        return redirect(url_for('uploads.gc_metrics_file'))
    metric_names = sorted(mf.csv_column_names())
    metric_names = list(filter(lambda n: n not in metric_blacklist,
                               metric_names))
    choices = list(zip(metric_names, metric_names))
    form.load_metric_choice.choices = choices
    form.perf_metric_choice.choices = choices

    if form.validate_on_submit():
        if current_user.has_pending_jobs(jobtype):
            m = 'Sorry, this type of job is already pending for you.'
        else:
            if jobtype == JobType.ff_fitting:
                algo = 'SLSQP'
            else:
                algo = 'LEAST_SQUARES'
            load_metric = form.load_metric_choice.data
            perf_metric = form.perf_metric_choice.data
            fitting_task.delay(current_user.id, load_metric, perf_metric, algo)

            '''perf_metric = '60 min Peak Power'
            # perf_metric = '60m_critical_power'
            # perf_metric = '60min Leistungsmaximum'
            algos = ['LEAST_SQUARES', 'L-BFGS-B', 'TNC', 'SLSQP', 'CMA-ES',
                     'DE']
            load_metrics = ['BikeScore', 'TSS', 'TRIMP Points',
                            'TRIMP Zonal Points', 'TRIMP(100) Points']
            # load_metrics = ['skiba_bike_score', 'coggan_tss', 'trimp_points',
            #               'trimp_zonal_points', 'trimp_100_points']
            # load_metrics = ['BikeScore', 'TSS', 'TRIMP Punkte',
            #               'TRIMP Punkte für Zonen', 'TRIMP(100) Punkte']
            for algo in algos:
                for load_metric in load_metrics:
                    t = fitting_task.delay(current_user.id,
                                           load_metric,
                                           perf_metric,
                                           algo)
                    t.get()
                    print('algo {} for metric {} finished'.format(algo,
                                                                  load_metric))
            '''
            m = Markup('Parameter fitting for {} has been started.<br>'
                       'Depending on server load, this can take a while.<br>'
                       'We\'ll mail you a notification when the job is done.'.
                       format(model_name))
        flash(m)
        return redirect(url_for('main.index'))

    default_load_metric_idx = default_selection_index(mf.default_load_metric(),
                                                      metric_names)
    default_perf_metric_idx = default_selection_index(mf.default_perf_metric(),
                                                      metric_names)
    return render_template('training/fitting.html',
                           form=form,
                           model_name=model_name,
                           default_load_metric_index=default_load_metric_idx,
                           default_perf_metric_index=default_perf_metric_idx)


def default_selection_index(defaults, choices):
    '''returns index in choices of the first element that's also in the given
    defaults list, otherwise 0'''
    for d in defaults:
        if d in choices:
            return choices.index(d)
    return 0


@training.route('/ff_genplan', methods=['GET', 'POST'])
@login_required
def ff_genplan():
    form = GeneratePlanForm()
    mf = current_user.gc_metrics_file.first()
    if mf is None:
        flash('First upload your GoldenCheetah metrics file.')
        return redirect(url_for('uploads.gc_metrics_file'))
    ff_parms = current_user.ff_parameters.first()
    if ff_parms is None:
        flash('First start your Fitness Fatigue parameter fitting')
        return redirect(url_for('training.ff_fitting'))
    if current_user.is_over_ff_plans_limit():
        flash(Markup('Sorry, you have reached the limit of {} '
                     'Fitness Fatigue plans.<br>'
                     'Delete some to generate new ones.'.format(PLANS_LIMIT)))
        return redirect(url_for('training.ff_myplans'))

    if form.validate_on_submit():
        if current_user.has_pending_jobs(JobType.ff_genplan):
            m = 'Sorry, this type of job is already pending for you.'
        else:
            if form.min_load.data is None:
                min_load = 0.0
            else:
                min_load = float(form.min_load.data)
            must_have_metrics = [ff_parms.load_metric, ff_parms.perf_metric]
            start_date = next_monday_after(mf.last_training(must_have_metrics))
            start_perf = current_user.ff_next_monday_p()
            off_weeks = sorted(parse_comma_separated_ints(form.off_weeks.data))
            off_weeks = dec_list_elems(off_weeks)   # users start at index 1
            off_day_dates = parse_comma_separated_dates(form.off_days.data)
            off_day_indexes = dates_to_indexes(start_date,
                                               off_day_dates,
                                               int(form.length.data))
            plan_request = PlanRequest(name=form.name.data.strip(),
                                       model_parms=ff_parms,
                                       start_date=start_date,
                                       start_perf=start_perf,
                                       goal=float(form.goal.data),
                                       length=int(form.length.data),
                                       max_load=float(form.max_load.data),
                                       min_load=min_load,
                                       off_weeks=off_weeks,
                                       off_days=off_day_indexes,
                                       weekly_cycle=parse_cycle_days(form))
            ff_genplan_task.delay(current_user.id, plan_request)
            # ff_genplan_cmaes_task.delay(current_user.id, plan_request)
            m = Markup('Fitness Fatigue plan generation has been started.<br>'
                       'Depending on server load, this can take a while.<br>'
                       'We\'ll mail you a notification when the job is done.')
        flash(m)
        return redirect(url_for('main.index'))
    try:
        next_monday_p = current_user.ff_next_monday_p()
        must_have_metrics = [ff_parms.load_metric, ff_parms.perf_metric]
        start_date = next_monday_after(mf.last_training(must_have_metrics))
        form.max_load.label.text += \
            ' (e.g. 100 {})*'.format(ff_parms.load_metric)
        return render_template('training/genplan.html',
                               form=form,
                               model='Fitness Fatigue',
                               next_monday=start_date,
                               next_monday_p=next_monday_p)
    except:
        print("ff_genplan(): ", sys.exc_info()[0])
        m = Markup("Unfortunately your metrics export file can't be parsed.<br>"
                   "Please check if a needed column is missing or any values "
                   "are mangled.<br>"
                   "You can upload a new metrics export anytime.<br>"
                   "Please contact us, if you are sure your data is correct.")
        flash(m)
        return redirect(url_for('main.index'))


@training.route('/pp_genplan', methods=['GET', 'POST'])
@login_required
def pp_genplan():
    form = GeneratePlanForm()
    mf = current_user.gc_metrics_file.first()
    if mf is None:
        flash('First upload your GoldenCheetah metrics file.')
        return redirect(url_for('uploads.gc_metrics_file'))
    pp_parms = current_user.pp_parameters.first()
    if pp_parms is None:
        flash('First start your PerPot parameter fitting')
        return redirect(url_for('training.pp_fitting'))
    if current_user.is_over_pp_plans_limit():
        flash(Markup('Sorry, you have reached the limit of {} PerPot plans.<br>'
                     'Delete some to generate new ones.'.
                     format(PLANS_LIMIT)))
        return redirect(url_for('training.pp_myplans'))

    if form.validate_on_submit():
        if current_user.has_pending_jobs(JobType.pp_genplan):
            m = 'Sorry, this type of job is already pending for you.'
        else:
            must_have_metrics = [pp_parms.load_metric, pp_parms.perf_metric]
            start_date = next_monday_after(mf.last_training(must_have_metrics))
            start_perf = current_user.pp_next_monday_pp()
            off_weeks = sorted(parse_comma_separated_ints(form.off_weeks.data))
            off_weeks = dec_list_elems(off_weeks)   # users start at index 1
            off_day_dates = parse_comma_separated_dates(form.off_days.data)
            off_day_indexes = dates_to_indexes(start_date,
                                               off_day_dates,
                                               int(form.length.data))
            goal = pp_parms.scale_perf_value(float(form.goal.data))
            max_load = pp_parms.scale_load_value(float(form.max_load.data))
            if form.min_load.data is None:
                min_load = 0.0
            else:
                min_load = pp_parms.scale_load_value(float(form.min_load.data))
            plan_request = PlanRequest(name=form.name.data.strip(),
                                       model_parms=pp_parms,
                                       start_date=start_date,
                                       start_perf=start_perf,
                                       goal=goal,
                                       length=int(form.length.data),
                                       max_load=max_load,
                                       min_load=min_load,
                                       off_weeks=off_weeks,
                                       off_days=off_day_indexes,
                                       weekly_cycle=parse_cycle_days(form))

            pp_genplan_task.delay(current_user.id, plan_request)
            # pp_genplan_cmaes_task.delay(current_user.id, plan_request)
            m = Markup('PerPot plan generation has been started.<br>'
                       'Depending on server load, this can take a while.<br>'
                       'We\'ll mail you a notification when the job is done.')
        flash(m)
        return redirect(url_for('main.index'))
    try:
        next_monday_pp_scaled = current_user.pp_next_monday_pp()
        print('next_monday_pp_scaled {}'.format(next_monday_pp_scaled))
        next_monday_pp = pp_parms.unscale_perf_value(next_monday_pp_scaled)
        print('next_monday_pp {}'.format(next_monday_pp))
        must_have_metrics = [pp_parms.load_metric, pp_parms.perf_metric]
        start_date = next_monday_after(mf.last_training(must_have_metrics))
        form.max_load.label.text += \
            ' (e.g. 100 {})*'.format(pp_parms.load_metric)
        return render_template('training/genplan.html',
                               form=form,
                               model='PerPot',
                               next_monday=start_date,
                               next_monday_p=next_monday_pp)
    except:
        m = Markup("Unfortunately your metrics export file can't be parsed.<br>"
                   "Please check if a needed column is missing or any values "
                   "are mangled.<br>"
                   "You can upload a new metrics export anytime.<br>"
                   "Please contact us, if you are sure your data is correct.")
        flash(m)
        return redirect(url_for('main.index'))


def parse_cycle_days(form):
    '''returns a WeekDay list for the chosen weekly training days'''
    days = [form.mondays.data, form.tuesdays.data, form.wednesdays.data,
            form.thursdays.data, form.fridays.data, form.saturdays.data,
            form.sundays.data]
    pairs = zip(days, list(WeekDays))
    return [pair[1] for pair in pairs if pair[0] is True]


def dec_list_elems(l):
    '''returns the given list with decremented elements'''
    return list(map(lambda x: x - 1, l))


@training.route('/ff_myplans', methods=['GET', 'POST'])
@login_required
def ff_myplans():
    details_form = ShowPlanForm()
    delete_form = DeletePlanForm()
    plans = current_user.ff_plans.order_by(FFPlan.id)
    # show details request out of list
    if request.method == 'POST' and \
            request.form['submit'] == 'Show Details' and \
            details_form.validate_on_submit():
        plan = plans.filter_by(id=details_form.plan_id_field.data).first()
        if plan is not None and plan.owner_id == current_user.id:
            form = DeletePlanForm()
            form.plan_id_field.data = plan.id
            return render_template('training/ff_plan.html',
                                   plan=plan,
                                   delete_form=form)
        else:
            return redirect(url_for('main.index'))
    # delete plan request
    elif request.method == 'POST' and \
            request.form['submit'] == 'Delete Plan' and \
            delete_form.validate_on_submit():
        plan = plans.filter_by(id=delete_form.plan_id_field.data).first()
        if plan is not None and plan.owner_id == current_user.id:
            print('deleting plan {}'.format(plan.id))
            db.session.delete(plan)
            db.session.commit()
            return redirect(url_for('training.ff_myplans'))
        else:
            return redirect(url_for('main.index'))
    # construct list overview
    else:
        details_forms = []
        delete_forms = []
        for plan in plans:
            sf = ShowPlanForm()
            sf.plan_id_field.data = plan.id
            details_forms.append(sf)
            df = DeletePlanForm()
            df.plan_id_field.data = plan.id
            delete_forms.append(df)
        plans_and_forms = zip(plans, details_forms, delete_forms)
        return render_template('training/myplans.html',
                               model='Fitness Fatigue',
                               plans_and_forms=plans_and_forms)


@training.route('/pp_myplans', methods=['GET', 'POST'])
@login_required
def pp_myplans():
    details_form = ShowPlanForm()
    delete_form = DeletePlanForm()
    plans = current_user.pp_plans.order_by(PPPlan.id)
    # show details request out of list
    if request.method == 'POST' and \
            request.form['submit'] == 'Show Details' and \
            details_form.validate_on_submit():
        plan = plans.filter_by(id=details_form.plan_id_field.data).first()
        if plan is not None and plan.owner_id == current_user.id:
            form = DeletePlanForm()
            form.plan_id_field.data = plan.id
            return render_template('training/pp_plan.html',
                                   plan=plan,
                                   delete_form=form)
        else:
            return redirect(url_for('main.index'))
    # delete plan request
    elif request.method == 'POST' and \
            request.form['submit'] == 'Delete Plan' and \
            delete_form.validate_on_submit():
        plan = plans.filter_by(id=delete_form.plan_id_field.data).first()
        if plan is not None and plan.owner_id == current_user.id:
            print('deleting plan {}'.format(plan.id))
            db.session.delete(plan)
            db.session.commit()
            return redirect(url_for('training.pp_myplans'))
        else:
            return redirect(url_for('main.index'))
    # construct list overview
    else:
        details_forms = []
        delete_forms = []
        for plan in plans:
            sf = ShowPlanForm()
            sf.plan_id_field.data = plan.id
            details_forms.append(sf)
            df = DeletePlanForm()
            df.plan_id_field.data = plan.id
            delete_forms.append(df)
        plans_and_forms = zip(plans, details_forms, delete_forms)
        return render_template('training/myplans.html',
                               model='PerPot',
                               plans_and_forms=plans_and_forms)
