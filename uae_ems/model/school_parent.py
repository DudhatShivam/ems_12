import time
from odoo import models, fields, api

class Relationship(models.Model):
    _name = "relationship"

    name = fields.Char(string="Name", required=True)


class Schoolparent(models.Model):
    _name = "school.parent"
    _description = "School parent information"

    son_of_employee = fields.Boolean(string='Son of Employee')
    is_black_list = fields.Boolean(string='Is Black List')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    guardian_id_number = fields.Char(string='ID Number')
    guardian_id_issued_place = fields.Many2one('res.country', string='Issued Place')
    guardian_id_expiry_date = fields.Date(string='Expiry Date')
    guardian_arabic_name = fields.Char(string='Arabic Name')
    guardian_relationship_student = fields.Many2one('relationship', string='Relationship')
    guardian_nationality = fields.Many2one('res.country', string='Nationality')
    guardian_passport_no = fields.Char(string='Passport No')
    guardian_passport_issued_place = fields.Many2one('res.country', string='Issued Place')
    guardian_passport_expiry_date = fields.Date(string='Expiry Date')
    guardian_address = fields.Text(string='Address')
    guardian_work_address = fields.Text(string='Work Address')
    guardian_home_tel = fields.Char(string='Home Tel')
    guardian_mobile1 = fields.Char(string='Mobile No1')
    guardian_mobile2 = fields.Char(string='Mobile No2')
    guardian_email = fields.Char(string='Email')
    guardian_work = fields.Char(string='work')
    guardian_document = fields.Char(string='Document')
    partner_id = fields.Many2one('res.partner', string='User ID', ondelete="cascade", delegate=True, required=True)
    guardian_phone = fields.Char(string='Phone')
