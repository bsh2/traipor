import csv
import re
import sys
from datetime import date, datetime, timedelta
from enum import Enum
from flask import current_app
from flask.ext.login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.dialects import postgresql
from sqlalchemy import Float

from app import db
from app import login_manager


PLANS_LIMIT = 25


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, index=True)
    username = db.Column(db.String(128), unique=True, index=True)
    password_hash = db.Column(db.String, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    accept_legalese = db.Column(db.Boolean, nullable=False)
    sex = db.Column(db.Integer)
    birth_year = db.Column(db.Integer)
    size = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    gc_metrics_file = db.relationship('GCMetricsFile',
                                      backref='owner',
                                      lazy='dynamic',
                                      cascade='all, delete-orphan')
    ff_parameters = db.relationship('FFParameters',
                                    backref='owner',
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    ff_plans = db.relationship('FFPlan',
                               backref='owner',
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    pp_parameters = db.relationship('PPParameters',
                                    backref='owner',
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    pp_plans = db.relationship('PPPlan',
                               backref='owner',
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    pending_jobs = db.relationship('PendingJob',
                                   backref='owner',
                                   lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password,
                                                    method='pbkdf2:sha512')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=86400):  # 24h expiration
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def generate_reset_token(self, expiration=86400):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def has_pending_jobs(self, jobtype=None):
        if jobtype is None:
            return self.pending_jobs.count() > 0
        for j in self.pending_jobs:
            if j.job_type == jobtype:
                return True

    def is_over_ff_plans_limit(self):
        print('is_over_ff_plans_limit {}'.format(self.ff_plans.count()))
        return self.ff_plans.count() > PLANS_LIMIT

    def is_over_pp_plans_limit(self):
        print('is_over_pp_plans_limit {}'.format(self.pp_plans.count()))
        return self.pp_plans.count() > PLANS_LIMIT

    def ff_current_p(self):
        '''returns the FF modeled performance for today'''
        from .training import fitnessfatigue as ff
        mf = self.gc_metrics_file.first()
        if mf is None:
            print('User {} has no gc_metrics_file'.format(self.id))
            return None
        ff_parms = self.ff_parameters.first()
        if ff_parms is None:
            print('User {} has no ff_parameters'.format(self.id))
            return None
        try:
            plan = ff_parms.plan_since_initial_p_till_today()
            print('plan leading to today {}'.format(plan))
            return ff.after_plan(plan, **ff_parms.to_dict())
        except:
            print('User.ff_current_p(): ', sys.exc_info()[0])
            return None

    def ff_next_monday_p(self):
        '''returns the FF modeled performance for next monday'''
        from .training import fitnessfatigue as ff
        mf = self.gc_metrics_file.first()
        if mf is None:
            print('User {} has no gc_metrics_file'.format(self.id))
            return None
        ff_parms = self.ff_parameters.first()
        if ff_parms is None:
            print('User {} has no ff_parameters'.format(self.id))
            return None
        try:
            plan = ff_parms.plan_since_initial_p_till_next_monday()
            print('plan leading to next monday {}'.format(plan))
            return ff.after_plan(plan, **ff_parms.to_dict())
        except:
            print('User.ff_next_monday_p(): ', sys.exc_info()[0])
            return None

    def pp_next_monday_pp(self):
        '''returns the PP modeled performance for next monday'''
        from .training import perpot as pp
        mf = self.gc_metrics_file.first()
        if mf is None:
            print('User {} has no gc_metrics_file'.format(self.id))
            return None
        pp_parms = self.pp_parameters.first()
        if pp_parms is None:
            print('User {} has no pp_parameters'.format(self.id))
            return None
        try:
            plan = pp_parms.plan_since_initial_pp_till_next_monday()
            print('plan leading to next monday {}'.format(plan))
            return pp.after_plan(plan, **pp_parms.to_dict())
        except:
            print('User.pp_next_monday_pp(): {}'.format(sys.exc_info()))
            return None

    def __repr__(self):
        return '<User {} {} {}>'.format(self.id, self.email, self.username)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class GCMetricsFile(db.Model):
    __tablename__ = 'gc_metrics_files'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.LargeBinary, nullable=False)
    upload_date = db.Column(db.Date, default=date.today(), nullable=False)
    is_complete = db.Column(db.Boolean, nullable=False)
    train_weekly_at_limits = db.Column(db.Boolean, nullable=False)
    with_power_meter = db.Column(db.Boolean, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def default_load_metric(self):
        '''choose load metric names depending on the sensor setup of the user'''
        if self.with_power_meter:
            return ['skiba_bike_score', 'BikeScore']
        else:
            return ['trimp_points', 'TRIMP Points', 'TRIMP Punkte']

    def default_perf_metric(self):
        '''choose perf metric names depending on the sensor setup of the user.
        for now just choose 60m_critical_power.
        '''
        return ['60m_critical_power', '60min Leistungsmaximum',
                '60 min Peak Power']

    def to_csv_dic(self, must_have_metrics=None, drop_history=True):
        '''returns the content of the metrics file as a dictionary'''
        from .training import fitting_util as f_util
        csvlines = self._decode_data()
        if drop_history:
            csvlines = self._drop_before_last_year(csvlines)
        return f_util.csv_value_dict_from_iter(csvlines, must_have_metrics)

    def csv_column_names(self):
        '''returns list of csv column names'''
        csvlines = self._decode_data()
        dictreader = csv.DictReader(csvlines)
        return list(map(lambda n: n.strip(), dictreader.fieldnames))

    def last_training(self, must_have_metrics):
        '''returns date of last training as date object'''
        csvdic = self.to_csv_dic(must_have_metrics, False)
        last = csvdic['date'][-1]
        try:
            m = re.fullmatch('[1]?[0-9]/[123]?[0-9]/\d\d\d\d', last)
            prep_date = ''
            if m is not None:
                d, m, y = last.split('/')
                prep_date = '{}/{}/{}'.format(d.zfill(2), m.zfill(2), y[2:4])
            else:
                prep_date = last
            return datetime.strptime(prep_date, '%m/%d/%y').date()
        except:
            print("GCMetricsFile.last_training(): ", sys.exc_info()[0])
            raise

    def days_since_last_training(self, must_have_metrics):
        '''returns number of days since the last training, excluding today'''
        last_training = self.last_training(must_have_metrics)
        print('last_training = {}'.format(last_training))
        if date.today() == last_training:
            since_last_training = 0
        else:
            since_last_training = (date.today() - last_training).days - 1
        print('since_last_training = {}'.format(since_last_training))
        return since_last_training

    def _decode_data(self):
        '''try to decode self.data with different encodings before ignoring any
        errors'''
        try:
            return self.data.decode('utf-8', errors='strict').splitlines()
        except UnicodeError:
            pass
        try:
            return self.data.decode('latin_1', errors='strict').splitlines()
        except UnicodeError:
            pass
        return self.data.decode('utf-8', errors='ignore').splitlines()

    def _drop_before_last_year(self, csv_lines):
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

    def __repr__(self):
        return '<GC_Metrics {} {} owned by {}>'.format(self.id,
                                                       str(self.upload_date),
                                                       self.owner_id)


class FFParameters(db.Model):
    __tablename__ = 'ff_parameters'
    id = db.Column(db.Integer, primary_key=True)
    initial_p = db.Column(db.Float, nullable=False)
    k_1 = db.Column(db.Float, nullable=False)
    tau_1 = db.Column(db.Float, nullable=False)
    k_2 = db.Column(db.Float, nullable=False)
    tau_2 = db.Column(db.Float, nullable=False)
    # metrics used for fitting
    load_metric = db.Column(db.String(128), nullable=False)
    perf_metric = db.Column(db.String(128), nullable=False)
    # contains the GC metrics file loads since the chosen initial_p to the end
    plan_since_initial_p = db.Column(postgresql.ARRAY(Float))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def plan_since_initial_p_till_today(self):
        user = User.query.get(self.owner_id)
        mf = user.gc_metrics_file.first()
        if mf is None:
            return None
        return self.plan_since_initial_p + \
            [0.0] * mf.days_since_last_training([self.load_metric,
                                                 self.perf_metric])

    def plan_since_initial_p_till_next_monday(self):
        from .training import plan_util as p_util
        user = User.query.get(self.owner_id)
        mf = user.gc_metrics_file.first()
        if mf is None:
            print('User {} has no gc_metrics_file'.format(user.id))
            return None
        last_training = mf.last_training([self.load_metric, self.perf_metric])
        days_between = \
            p_util.days_between_last_training_and_next_monday(last_training)
        print('days_between = {}'.format(days_between))
        return self.plan_since_initial_p + [0.0] * days_between

    def to_dict(self):
        d = {}
        d['initial_p'] = self.initial_p
        d['k_1'] = self.k_1
        d['tau_1'] = self.tau_1
        d['k_2'] = self.k_2
        d['tau_2'] = self.tau_2
        return d

    def __repr__(self):
        return '<FFParameters {} {} {} {} {} {} {}>'.format(self.id,
                                                            self.owner_id,
                                                            self.initial_p,
                                                            self.k_1,
                                                            self.tau_1,
                                                            self.k_2,
                                                            self.tau_2)


class FFPlan(db.Model):
    __tablename__ = 'ff_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    start_date = db.Column(db.Date, nullable=False)
    start_perf = db.Column(db.Float, nullable=False)
    end_perf = db.Column(db.Float, nullable=False)
    loads = db.Column(postgresql.ARRAY(db.Float), nullable=False)
    # FFParameters used for plan generation
    initial_p = db.Column(db.Float, nullable=False)
    k_1 = db.Column(db.Float, nullable=False)
    tau_1 = db.Column(db.Float, nullable=False)
    k_2 = db.Column(db.Float, nullable=False)
    tau_2 = db.Column(db.Float, nullable=False)
    load_metric = db.Column(db.String(128), nullable=False)
    perf_metric = db.Column(db.String(128), nullable=False)
    # contains the loads since initial_p up to self.start_date
    prequel_plan = db.Column(postgresql.ARRAY(db.Float))
    # constraints
    goal = db.Column(db.Float, nullable=False)
    length = db.Column(db.Integer, nullable=False)  # in weeks
    max_load = db.Column(db.Float, nullable=False)
    min_load = db.Column(db.Float, default=0.0)
    off_weeks = db.Column(postgresql.ARRAY(db.Integer))
    off_days = db.Column(postgresql.ARRAY(db.Integer))
    weekly_cycle = db.Column(postgresql.ARRAY(db.Integer), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def ui_start_perf(self):
        return self.start_perf

    def ui_end_perf(self):
        return self.end_perf

    def ui_goal(self):
        return self.goal

    def ui_max_load(self):
        return self.max_load

    def ui_min_load(self):
        return self.min_load

    def ui_loads(self):
        return self.loads

    def ui_off_weeks(self):
        weeks = list(map(lambda x: x + 1, self.off_weeks))
        if len(weeks) > 0:
            return str(weeks).strip('[]')
        else:
            return ''

    def ui_weekly_cycle(self):
        from .training import plan_util
        l = ''
        for d in self.weekly_cycle:
            l += plan_util.WeekDays.to_short_str(d) + ', '
        return l.rstrip(', ')

    def to_calendar(self):
        '''returns a list of formated date load lines'''
        delta1 = timedelta(days=1)
        date = self.start_date
        plan_calendar = [0] * len(self.loads)
        for i, load in enumerate(self.loads):
            plan_calendar[i] = '{} {:.2f}'.format(date, load)
            date += delta1
        return plan_calendar


class PPParameters(db.Model):
    __tablename__ = 'pp_parameters'
    id = db.Column(db.Integer, primary_key=True)
    strainpot = db.Column(db.Float, nullable=False)
    responsepot = db.Column(db.Float, nullable=False)
    perfpot = db.Column(db.Float, nullable=False)   # aka the initial_pp
    straindelay = db.Column(db.Float, nullable=False)
    responsedelay = db.Column(db.Float, nullable=False)
    overflowdelay = db.Column(db.Float, nullable=False)
    # scaling factors for plan and performance values
    load_scale_factor = db.Column(db.Float, nullable=False)
    perf_scale_factor = db.Column(db.Float, nullable=False)
    # metrics used for fitting
    load_metric = db.Column(db.String(128), nullable=False)
    perf_metric = db.Column(db.String(128), nullable=False)
    # contains the GC metrics file loads since the chosen initial_pp to the end
    plan_since_initial_pp = db.Column(postgresql.ARRAY(Float))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def unscale_perf_value(self, value):
        return value * (self.perf_scale_factor**-1)

    def scale_perf_value(self, value):
        return value * self.perf_scale_factor

    def scale_load_value(self, value):
        return value * self.load_scale_factor

    def plan_since_initial_pp_till_next_monday(self):
        from .training import plan_util as p_util
        user = User.query.get(self.owner_id)
        mf = user.gc_metrics_file.first()
        if mf is None:
            print('User {} has no gc_metrics_file'.format(user.id))
            return None
        last_training = mf.last_training([self.load_metric, self.perf_metric])
        days_between = \
            p_util.days_between_last_training_and_next_monday(last_training)
        print('days_between = {}'.format(days_between))
        return self.plan_since_initial_pp + [0.0] * days_between

    def to_dict(self):
        d = {}
        d['strainpot'] = self.strainpot
        d['responsepot'] = self.responsepot
        d['perfpot'] = self.perfpot
        d['straindelay'] = self.straindelay
        d['responsedelay'] = self.responsedelay
        d['overflowdelay'] = self.overflowdelay
        return d

    def __repr__(self):
        return '<FFParameters {} {} {} {} {} {} {}>'.format(self.id,
                                                            self.owner_id,
                                                            self.strainpot,
                                                            self.responsepot,
                                                            self.perfpot,
                                                            self.straindelay,
                                                            self.responsedelay,
                                                            self.overflowdelay)


class PPPlan(db.Model):
    __tablename__ = 'pp_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    start_date = db.Column(db.Date, nullable=False)
    start_perf = db.Column(db.Float, nullable=False)
    end_perf = db.Column(db.Float, nullable=False)
    loads = db.Column(postgresql.ARRAY(db.Float), nullable=False)
    # PPParameters used for plan generation
    strainpot = db.Column(db.Float, nullable=False)
    responsepot = db.Column(db.Float, nullable=False)
    perfpot = db.Column(db.Float, nullable=False)   # aka the initial_pp
    straindelay = db.Column(db.Float, nullable=False)
    responsedelay = db.Column(db.Float, nullable=False)
    overflowdelay = db.Column(db.Float, nullable=False)
    load_scale_factor = db.Column(db.Float, nullable=False)
    perf_scale_factor = db.Column(db.Float, nullable=False)
    load_metric = db.Column(db.String(128), nullable=False)
    perf_metric = db.Column(db.String(128), nullable=False)
    # contains the loads since initial_pp up to self.start_date
    prequel_plan = db.Column(postgresql.ARRAY(db.Float))
    # constraints
    goal = db.Column(db.Float, nullable=False)
    length = db.Column(db.Integer, nullable=False)  # in weeks
    max_load = db.Column(db.Float, nullable=False)
    min_load = db.Column(db.Float, default=0.0)
    off_weeks = db.Column(postgresql.ARRAY(db.Integer))
    off_days = db.Column(postgresql.ARRAY(db.Integer))
    weekly_cycle = db.Column(postgresql.ARRAY(db.Integer), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def unscale_perf_value(self, value):
        return value * (self.perf_scale_factor**-1)

    def unscale_load_value(self, value):
        return value * (self.load_scale_factor**-1)

    def ui_start_perf(self):
        return self.unscale_perf_value(self.start_perf)

    def ui_end_perf(self):
        return self.unscale_perf_value(self.end_perf)

    def ui_goal(self):
        return self.unscale_perf_value(self.goal)

    def ui_max_load(self):
        return self.unscale_load_value(self.max_load)

    def ui_min_load(self):
        return self.unscale_load_value(self.min_load)

    def ui_loads(self):
        return list(map(self.unscale_load_value, self.loads))

    def ui_off_weeks(self):
        weeks = list(map(lambda x: x + 1, self.off_weeks))
        if len(weeks) > 0:
            return str(weeks).strip('[]')
        else:
            return ''

    def ui_weekly_cycle(self):
        from .training import plan_util
        l = ''
        for d in self.weekly_cycle:
            l += plan_util.WeekDays.to_short_str(d) + ', '
        return l.rstrip(', ')

    def to_calendar(self):
        '''returns a list of formated date load lines'''
        delta1 = timedelta(days=1)
        date = self.start_date
        plan_calendar = [0] * len(self.loads)
        for i, load in enumerate(self.ui_loads()):
            plan_calendar[i] = '{} {:.2f}'.format(date, load)
            date += delta1
        return plan_calendar


class JobType(Enum):
    ff_fitting = 1
    ff_genplan = 2
    pp_fitting = 3
    pp_genplan = 4

    def to_str(self):
        strings = ['FF Parameter Fitting', 'FF Plan Generation',
                   'PP Parameter Fitting', 'PP Plan Generation']
        return strings[self.value - 1]


class PendingJob(db.Model):
    __tablename__ = 'pending_jobs'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    _job_type = db.Column(db.Integer, nullable=False)
    creation_time = db.Column(db.DateTime(),
                              default=datetime.utcnow,
                              nullable=False)

    @property
    def job_type(self):
        return JobType(self._job_type)

    @job_type.setter
    def job_type(self, jobtype):
        self._job_type = jobtype.value

    def __repr__(self):
        return '<PendingJob> {} {} {} {}'.format(self.id,
                                                 self.owner_id,
                                                 self.job_type,
                                                 self.creation_time)
