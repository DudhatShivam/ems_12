import time
from odoo import models, fields, api
from odoo.exceptions import UserError


class StudentFeesStructureLine(models.Model):
    '''Student Fees Structure Line'''
    _name = 'student.fees.structure.line'
    _description = 'Student Fees Structure Line'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    type = fields.Selection([('month', 'Monthly'),
                             ('year', 'Yearly'),
                             ('range', 'Range')],
                            string='Duration Type', required=True)
    amount = fields.Float(string='Amount', digits=(16, 2))
    sequence = fields.Integer(string='Sequence')
    # line_ids = fields.One2many('student.payslip.line.line', 'slipline1_id', string='Calculations')
    account_id = fields.Many2one('account.account', string="Account")
    company_id = fields.Many2one('res.company', string='Company',
                                 change_default=True,
                                 default=lambda obj_c: obj_c.env['res.users'].
                                 browse([obj_c._uid])[0].company_id)
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_symbol = fields.Char(related="currency_id.symbol", string='Symbol')

    arabic_name = fields.Char(string='Arabic Name')
    classes = fields.Many2one('standard.standard', string='Class', required=True)
    academic_year = fields.Many2one('academic.year', string='Academic Years')
    duration = fields.Char(string='Duration')

    @api.onchange('company_id')
    def set_currency_company(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id.id


class StudentFeesStructure(models.Model):
    '''Fees structure'''
    _name = 'student.fees.structure'
    _description = 'Student Fees Structure'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    classes = fields.Many2one('standard.standard', string='Class', required=True)
    # line_ids = fields.Many2many('student.fees.structure.line',
    #                             'fees_structure_payslip_rel',
    #                             'fees_id', 'slip_id', string='Fees Structure')
    structure_line_ids = fields.One2many('fee.structure.line', 'student_fee_id', string='Fees Structure')
    academic_year = fields.Many2one('academic.year', string='Academic Years')

    _sql_constraints = [('code_uniq', 'unique(code)',
                         '''The code of the Fees Structure must
                         be unique !''')]

    _sql_constraints = [('unique_classes', 'unique(classes)',
                         "Structure of this class is already existed")]


class FeeStructureLine(models.Model):
    _name = "fee.structure.line"

    name = fields.Char(related='structre_line_id.name', string="name")
    structre_line_id = fields.Many2one('student.fees.structure.line', string="Fees Head")
    student_fee_id = fields.Many2one('student.fees.structure', string="Fee structure")
    amount = fields.Float(string="Amount")
    code = fields.Char(related='structre_line_id.code', string='Code')
    account_id = fields.Many2one(related='structre_line_id.account_id', string="Account")
    company_id = fields.Many2one(related='structre_line_id.company_id', string='Company', change_default=True, default=lambda obj_c: obj_c.env['res.users'].browse([obj_c._uid])[0].company_id)
    currency_id = fields.Many2one(related='structre_line_id.currency_id', string='Currency')
    currency_symbol = fields.Char(related="currency_id.symbol", string='Symbol')
    arabic_name = fields.Char(related='structre_line_id.arabic_name', string='Arabic Name')
    academic_year = fields.Many2one(related='structre_line_id.academic_year', string='Academic Years')
    sequence = fields.Integer(related='structre_line_id.sequence', string='Sequence')
    duration = fields.Char(related='structre_line_id.duration', string='Duration')
    classes = fields.Many2one(related='structre_line_id.classes', string='Class', required=True)

    type = fields.Selection([('month', 'Monthly'),
                             ('year', 'Yearly'),
                             ('range', 'Range')],
                            string='Duration', required=True, related="structre_line_id.type")


class EMSDiscount(models.Model):
    _name = 'ems.discount'
    _description = 'EMS Discount'

    name = fields.Char(string='Discount Name', required=True, translate=True)
    arabic_name = fields.Char(string='Arabic Name', translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    amount = fields.Float(required=True, digits=(16, 4))
    account_id = fields.Many2one('account.account', string='Discount Account')
    description = fields.Char(string='Label on Invoices', translate=True)
    school_id = fields.Many2one('school.school', string="School", required=True, copy=False)
    acadamic_year_id = fields.Many2one('academic.year', string="Study year")
    branch_id = fields.Many2one('student.branch', string="Branch")
    discount_type = fields.Selection([('both', 'Both'), ('fix', 'Fix Amount'), ('percentage', 'Percentage')], string="Discount Type", default="fix", required=True)
    amount_per = fields.Float(string="Discount %")
    amount = fields.Float(string="Amount", digits=(16, 4))
    brother_dic_for_bro = fields.Float(string="Brothers Discount")

    @api.model
    def create(self, vals):
        res = super(EMSDiscount, self).create(vals)
        if res.amount < 0 or res.amount > 100:
            raise UserError('Discount should be greater than 0/zero and less than 100.')
        return res

    @api.multi
    def write(self, vals):
        if vals.get('amount') < 0 or vals.get('amount') > 100:
            raise UserError('Discount should be greater than 0/zero and less than 100.')
        return super(EMSDiscount, self).write(vals)
