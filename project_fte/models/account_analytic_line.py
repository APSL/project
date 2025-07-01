from odoo import api, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._update_fte_month_lines()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._update_fte_month_lines()
        return res

    def unlink(self):
        fte_lines = self.env["project.fte.month.line"]
        for line in self:
            if line.project_id and line.date and not line.non_billable:
                fte_lines |= line._get_fte_line()

        res = super().unlink()

        if fte_lines:
            fte_lines._compute_executed_hours()
        return res

    def _update_fte_month_lines(self):
        for line in self:
            if not line.project_id or not line.date or line.non_billable:
                continue
            fte_line = line._get_fte_line()
            if fte_line:
                fte_line._compute_executed_hours()

    def _get_fte_line(self):
        self.ensure_one()
        if not self.project_id or not self.date or self.non_billable:
            return None
        fte_line = (
            self.env["project.fte.month.line"]
            .sudo()
            .search(
                [
                    ("project_id", "=", self.project_id.id),
                    ("month", "=", str(self.date.month)),
                    ("year", "=", self.date.year),
                ]
            )
        )
        return fte_line
