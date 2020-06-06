from odoo import models, fields, api, tools, _


class StudentType(models.Model):
    _name = 'student.type'
    _description = 'Student Type'

    name = fields.Char(string='Student Type')


class EducationLevel(models.Model):
    _name = 'education.level'
    _description = 'Education Level'

    name = fields.Char(string='Education Level')


class Classification(models.Model):
    _name = 'classification'
    _description = 'Classification'

    name = fields.Char(string='Classification')


class StudentBranch(models.Model):
    _name = 'student.branch'
    _description = 'Student Branch'

    name = fields.Char(string='Branch')
