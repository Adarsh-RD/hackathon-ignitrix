"""
returnX AI — Tax Calculator Tool
Deterministic tax computation used by TaxAdvisorAgent.
Implements Indian tax provisions for gig workers.
"""


class TaxCalculator:
    """
    Tool: compute_tax
    Calculates TDS, Section 44AD, and tax slab estimates.
    This is a deterministic tool (no LLM needed).
    """

    # New Tax Regime slabs FY 2025-26
    NEW_REGIME_SLABS = [
        (300000, 0.00),    # 0 - 3L: 0%
        (400000, 0.05),    # 3L - 7L: 5%
        (300000, 0.10),    # 7L - 10L: 10%
        (200000, 0.15),    # 10L - 12L: 15%
        (300000, 0.20),    # 12L - 15L: 20%
        (float('inf'), 0.30),  # 15L+: 30%
    ]

    def compute(self, total_income: float, total_expenses: float) -> dict:
        """
        Compute comprehensive tax breakdown.

        Args:
            total_income:   Total income amount
            total_expenses: Total expense amount

        Returns:
            dict with all tax computations
        """
        net_income = total_income - total_expenses

        # TDS at 1% (Section 194-O)
        tds = round(total_income * 0.01, 2)

        # Section 44AD: 6% of gross receipts is deemed taxable profit
        taxable_44ad = round(total_income * 0.06, 2)

        # Annual projections (assume data is monthly)
        annual_income = round(total_income * 12, 2)
        annual_expenses = round(total_expenses * 12, 2)
        annual_taxable_44ad = round(annual_income * 0.06, 2)

        # Tax on annual 44AD income under new regime
        tax_on_44ad = self._compute_slab_tax(annual_taxable_44ad)

        # Tax on regular income (income - expenses) under new regime
        annual_net = annual_income - annual_expenses
        tax_regular = self._compute_slab_tax(annual_net)

        # Effective tax rate
        effective_rate = (tax_on_44ad / annual_income * 100) if annual_income > 0 else 0

        # Recommend regime
        regime = "44AD_presumptive" if tax_on_44ad <= tax_regular else "regular"

        return {
            "tds": tds,
            "taxable_44ad": taxable_44ad,
            "net_income": round(net_income, 2),
            "annual_income_projected": annual_income,
            "annual_expenses_projected": annual_expenses,
            "annual_taxable_44ad": annual_taxable_44ad,
            "tax_on_44ad": round(tax_on_44ad, 2),
            "tax_regular": round(tax_regular, 2),
            "effective_rate": f"{effective_rate:.2f}%",
            "regime_recommended": regime,
            "savings_with_44ad": round(max(0, tax_regular - tax_on_44ad), 2),
        }

    def _compute_slab_tax(self, taxable_income: float) -> float:
        """Calculate tax under new regime slabs."""
        if taxable_income <= 0:
            return 0.0

        tax = 0.0
        remaining = taxable_income
        for slab_limit, rate in self.NEW_REGIME_SLABS:
            if remaining <= 0:
                break
            taxable_in_slab = min(remaining, slab_limit)
            tax += taxable_in_slab * rate
            remaining -= taxable_in_slab

        # Add 4% Health & Education Cess
        tax *= 1.04
        return round(tax, 2)
