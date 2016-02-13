from flask import flash
from flask.ext.wtf import Form
from wtforms import BooleanField, FloatField, IntegerField, StringField
from wtforms import HiddenField, SelectField, SubmitField
from wtforms.validators import NumberRange, Optional, Required, Regexp
from wtforms.validators import Length, ValidationError
from .plan_util import parse_comma_separated_ints, parse_comma_separated_dates


class StartFittingForm(Form):
    load_metric_choice = SelectField('Your preferred training load metric')
    perf_metric_choice = SelectField('Your preferred performance metric')
    submit = SubmitField('start fitting')

    def validate(self):
        if self.load_metric_choice.data != self.perf_metric_choice.data:
            different_metrics = True
        else:
            different_metrics = False
            flash("Your chosen load and performance metrics can't be the same.")
        return super().validate() and different_metrics


def validate_int_strings(form, field):
    '''raises a ValidationError if one of the ints in the field is < 1'''
    try:
        l = parse_comma_separated_ints(field.data)
    except:
        raise ValidationError('')
    if len(l) > 0:
        if min(l) < 1:
            raise ValidationError('this field starts counting at 1')


def validate_offdays(form, field):
    '''raises a ValidationError if field content isn't a comma separated list of
    yyyy-mm-dd'''
    try:
        parse_comma_separated_dates(field.data)
    except:
        raise ValidationError('bad date format')


class GeneratePlanForm(Form):
    r = '(^(\d+)$)|(^(\d+){1}(,\s*\d+)+$)'
    name = StringField('Name of the Plan',
                       validators=[Optional(True), Length(1, 128),
                                   Regexp('^[A-Za-z0-9][A-Za-z0-9_. ]*$', 0,
                                          'plan names must have only letters, '
                                          'numbers, dots or underscores')])
    goal = FloatField('Goal (e.g. your current performance + 10)*',
                      validators=[Required(), NumberRange(0.0)])
    length = IntegerField('Plan Length in Weeks (e.g. 12)*',
                          validators=[Required(), NumberRange(1, 52)])
    max_load = FloatField('Max Load Value',
                          validators=[Required(), NumberRange(0.0)])
    min_load = FloatField('Min Load Value',
                          default=0.0,
                          validators=[Optional(), NumberRange(0.0)])
    off_weeks = StringField('Off Weeks in Your Plan (e.g. 3, 7, 11)',
                            validators=[Optional(True), validate_int_strings,
                                        Regexp(r,
                                               0,
                                               'This field requires comma '
                                               'separated week numbers.')])
    off_days = HiddenField('', validators=[Optional(True), validate_offdays])
    mondays = BooleanField('Train on Mondays', default='checked')
    tuesdays = BooleanField('Train on Tuesdays', default='checked')
    wednesdays = BooleanField('Train on Wednesdays', default='checked')
    thursdays = BooleanField('Train on Thursdays')
    fridays = BooleanField('Train on Fridays', default='checked')
    saturdays = BooleanField('Train on Saturdays', default='checked')
    sundays = BooleanField('Train on Sundays')
    submit = SubmitField('Generate Plan', default='checked')

    def validate(self):
        super_val = super().validate()
        if not super_val:
            return False
        # validate min_load <= max_load
        if self.min_load.data is not None:
            min_load_le_max_load = self.min_load.data <= self.max_load.data
        else:
            min_load_le_max_load = True
        if not min_load_le_max_load:
            flash('Your minimum load must be smaller than your maximum load.')
        # validate if user allows at least one training day
        days = [self.mondays.data, self.tuesdays.data, self.wednesdays.data,
                self.thursdays.data, self.fridays.data, self.saturdays.data,
                self.sundays.data]
        at_least_one_day = any(days)
        if not at_least_one_day:
            flash('Harden up! You have to train at least one day per week.')
        # validate if user allows at least one training week
        try:
            l = parse_comma_separated_ints(self.off_weeks.data)
            if len(set(l)) >= self.length.data:
                flash('Harden up! You have to train in at least one week.')
                at_least_one_week = False
            else:
                at_least_one_week = True
        except:
            pass    # we deal with that in super().validate()
        return at_least_one_day and at_least_one_week and min_load_le_max_load


class ShowPlanForm(Form):
    plan_id_field = HiddenField('hidden', validators=[Required()])
    submit = SubmitField('Show Details')


class DeletePlanForm(Form):
    plan_id_field = HiddenField('hidden', validators=[Required()])
    submit = SubmitField('Delete Plan')
