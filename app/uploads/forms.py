from flask.ext.wtf import Form
from wtforms import BooleanField, FileField, SubmitField, RadioField
from wtforms.validators import Required


class UploadGCMetricsFileForm(Form):
    metrics_file = FileField('Your metrics file', validators=[Required()])
    is_complete = BooleanField('The data contains all my training sessions of \
                               the given timeframe.')
    with_power_meter = BooleanField('I use a real power meter in training.')
    choices = [('weekly', 'I go to my limits roughly each week of training.'),
               ('monthly', 'I go to my limits each month of training.')]
    train_at_limits = RadioField(choices=choices, validators=[Required()])
    submit = SubmitField('upload')
