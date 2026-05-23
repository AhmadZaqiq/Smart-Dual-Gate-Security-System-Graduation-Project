from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional


class SettingsForm(FlaskForm):
    submit = SubmitField("Save Settings")


class SettingFieldForm(FlaskForm):
    setting_key = StringField("Key", validators=[Optional()])
    setting_value = StringField("Value", validators=[Optional()])
