from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length

class TicketCreateForm(FlaskForm):
    
    subject       = StringField("Título", validators=[DataRequired(), Length(max=200)])
    details       = TextAreaField("Descripción", validators=[DataRequired(), Length(min=10)])
    category_id   = SelectField("Categoría", coerce=int, validators=[DataRequired()])
    department_id = SelectField("Departamento", coerce=int, validators=[DataRequired()])
    priority_id   = SelectField("Prioridad", coerce=int, validators=[DataRequired()])
    assignee_id   = SelectField("Asignar a", coerce=int)  # 0 = sin asignar
