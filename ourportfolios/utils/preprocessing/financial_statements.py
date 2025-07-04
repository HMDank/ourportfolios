from vnstock import Screener, Vnstock
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
screener = Screener(source="TCBS")
default_params = {
    "exchangeName": "HOSE,HNX",
    "marketCap": (2000, 99999999999),
}
df = screener.stock(default_params, limit=1700, lang="en")

def safe_get_multiindex(df, category, column_name, default=pd.NA):
    """
    Safely get data from MultiIndex DataFrame

    Args:
        df: MultiIndex DataFrame
        category: Level 0 category (e.g., "Chỉ tiêu cơ cấu nguồn vốn")
        column_name: Level 1 column name (e.g., "Debt/Equity")
        default: Default value if not found
    """
    try:
        if isinstance(df.columns, pd.MultiIndex):
            if (category, column_name) in df.columns:
                return df[(category, column_name)]
            else:
                return pd.Series([default] * len(df.index), index=df.index)
        else:
            # Fallback for regular columns
            if column_name in df.columns:
                return df[column_name]
            else:
                return pd.Series([default] * len(df.index), index=df.index)
    except Exception:
        return pd.Series([default] * len(df.index), index=df.index)


def analyze_fixed(
    ticker_symbol, source="VCI", period="year", lang="en"
):
    def calculate_yoy_growth(series):
        if len(series) < 2:
            return pd.Series(dtype=float, index=series.index)
        series_sorted = series.sort_index()
        return series_sorted.pct_change() * 100

    # Helper function to safely get column data (for regular DataFrames)
    def safe_get(df, column_name, default=pd.NA):
        if column_name in df.columns:
            return df[column_name]
        else:
            return pd.Series([default] * len(df.index), index=df.index)

    stock = Vnstock().stock(symbol=ticker_symbol, source=source)
    income_statement = stock.finance.income_statement(period=period, lang=lang)
    balance_sheet = stock.finance.balance_sheet(period=period, lang=lang)
    cash_flow = stock.finance.cash_flow(period=period, lang=lang)
    key_ratios = stock.finance.ratio(period=period, lang=lang)

    # Detect company type (bank vs non-bank)
    bank_indicators = [
        "Net Interest Income",
        "Interest and Similar Income",
        "Net Fee and Commission Income",
        "Provision for credit losses",
    ]
    bank_column_count = sum(
        1 for col in bank_indicators if col in income_statement.columns
    )
    is_bank = bank_column_count >= len(bank_indicators) // 2

    # === TRANSFORM INCOME STATEMENT ===
    income_df = income_statement.copy()
    transformed_income = pd.DataFrame()
    if not income_df.empty:
        transformed_income.index = income_df.index

    if is_bank:
        # Bank income statement mapping
        income_mapping = {
            "Year": "yearReport",
            "Quarter": "lengthReport" if period == "quarter" else None,
            "Net interest income": "Net Interest Income",
            "Interest and similar income": "Interest and Similar Income",
            "Interest and similar expenses": "Interest and Similar Expenses",
            "Net fee and commission income": "Net Fee and Commission Income",
            "Fees and commission income": "Fees and Comission Income",
            "Fees and commission expenses": "Fees and Comission Expenses",
            "Net gain (loss) from trading of foreign currencies": "Net gain (loss) from foreign currency and gold dealings",
            "Net gain from trading of held-for-trading securities": "Net gain (loss) from trading of trading securities",
            "Net gain from trading of investment securities": "Net gain (loss) from disposal of investment securities",
            "Net other income/expenses": "Net Other income/expenses",
            "Other income": "Net Other income/(expenses)",
            "Other expenses": "Other expenses",
            "Income from investments in other entities": "Dividends received",
            "Operating expenses": "General & Admin Expenses",
            "Operating income before allowance for credit losses": "Operating Profit before Provision",
            "Allowance expenses for credit losses": "Provision for credit losses",
            "Profit before tax": "Profit before tax",
            "Corporate income tax": "Tax For the Year",
            "Business income tax - current": "Business income tax - current",
            "Business income tax - deferred": "Business income tax - deferred",
            "Net Profit": "Net Profit For the Year",
            "Attributable to parent company": "Attributable to parent company",
            "Minority interest": "Minority Interest",
        }
    else:
        # Non-bank income statement mapping
        income_mapping = {
            "Year": "yearReport",
            "Quarter": "lengthReport" if period == "quarter" else None,
            "Sales": "Sales",
            "Sales deductions": "Sales deductions",
            "Net sales": "Net Sales",
            "Cost of goods sold": "Cost of Sales",
            "Gross profit": "Gross Profit",
            "Financial income": "Financial Income",
            "Financial expenses": "Financial Expenses",
            "Including: Interest expense": "Interest Expenses",
            "Selling expenses": "Selling Expenses",
            "General & administrative expenses": "General & Admin Expenses",
            "Operating income": "Operating Profit/Loss",
            "Other income (expense)": "Net other income/expenses",
            "Other income": "Other income",
            "Other expenses": "Other Income/Expenses",
            "Profit before tax": "Profit before tax",
            "Business income tax - current": "Business income tax - current",
            "Business income tax - deferred": "Business income tax - deferred",
            "Net profit": "Net Profit For the Year",
            "Attributable to parent company": "Attributable to parent company",
            "Minority interest": "Minority Interest",
        }

    # Apply income statement mappings
    for new_name, old_name in income_mapping.items():
        transformed_income[new_name] = safe_get(income_df, old_name)

    # Add ratio-based columns AFTER the mappings (at the end of the table)
    if is_bank:
        # Add ratio-based columns for banks using MultiIndex access
        transformed_income["EPS"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "EPS (VND)"
        )
        transformed_income["Outstanding Share"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "Outstanding Share (Mil. Shares)"
        )
    else:
        # Add ratio-based columns for non-banks using MultiIndex access
        transformed_income["EPS"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "EPS (VND)"
        )
        transformed_income["Outstanding Share"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "Outstanding Share (Mil. Shares)"
        )
        transformed_income["EBITDA"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "EBITDA (Bn. VND)"
        )
        transformed_income["EBIT"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "EBIT (Bn. VND)"
        )

    # === TRANSFORM BALANCE SHEET ===
    balance_df = balance_sheet.copy()
    transformed_balance = pd.DataFrame()
    if not balance_df.empty:
        transformed_balance.index = balance_df.index

    if is_bank:
        # Bank balance sheet mapping (same as before)
        balance_mapping = {
            "Year": "yearReport",
            "Quarter": "lengthReport" if period == "quarter" else None,
            "Assets": "TOTAL ASSETS (Bn. VND)",
            "Cash, gold and gemstones": "Cash and cash equivalents (Bn. VND)",
            "Balances with the State Bank of Vietnam (SBV)": "Balances with the SBV",
            "Deposits with and loans to other credit institutions (CIs)": "Placements with and loans to other credit institutions",
            "Net trading securities": "Trading Securities, net",
            "Trading securities": "Trading Securities",
            "Provision for trading securities": "Provision for diminution in value of Trading Securities",
            "Derivatives and other financial assets": "Derivatives and other financial liabilities",
            "Net loans to customers": "Loans and advances to customers, net",
            "Loans to customers": "Loans and advances to customers",
            "Provision for loans to customers": "Less: Provision for losses on loans and advances to customers",
            "Investment securities": "Investment Securities",
            "Available-for-sale securities": "Available-for Sales Securities",
            "Held-to-maturity securities": "Held-to-Maturity Securities",
            "Provision for investment securities": "Less: Provision for diminution in value of investment securities",
            "Long-term investments": "Long-term investments (Bn. VND)",
            "Other long-term investments": "Other long-term assets (Bn. VND)",
            "Provision for long-term investments": "Less: Provision for diminuation in value of long term investments",
            "Fixed assets": "Fixed assets (Bn. VND)",
            "Tangible fixed assets": "Tangible fixed assets",
            "Intangible fixed assets": "Intagible fixed assets",
            "Investment properties": "Investment in properties",
            "Other assets": "Other Assets",
            "Liabilities": "LIABILITIES (Bn. VND)",
            "Due to the Government and the SBV": "Due to Gov and borrowings from SBV",
            "Deposits and borrowings from other CIs": "Deposits and borrowings from other credit institutions",
            "Deposits from customers": "Deposits from customers",
            "Derivatives and other financial liabilities": "_Derivatives and other financial liabilities",
            "Other borrowed and entrusted funds": "Funds received from Gov, international and other institutions",
            "Valuable papers issued": "Convertible bonds/CDs and other valuable papers issued",
            "Other liabilities": "Other liabilities",
            "Shareholders' Equity": "OWNER'S EQUITY(Bn.VND)",
            "Share capital": "Capital",
            "Charter capital": "Paid-in capital (Bn. VND)",
            "Other capital": "Other Reserves",
            "Reserves": "Reserves",
            "Foreign exchange differences": "Foreign Currency Difference reserve",
            "Differences upon asset revaluation": "Difference upon Assets Revaluation",
            "Retained earnings": "Undistributed earnings (Bn. VND)",
            "Minority interests": "MINORITY INTERESTS",
        }
    else:
        # Non-bank balance sheet mapping (same as before)
        balance_mapping = {
            "Year": "yearReport",
            "Quarter": "lengthReport" if period == "quarter" else None,
            "TOTAL ASSETS": "TOTAL ASSETS (Bn. VND)",
            "CURRENT ASSETS": "CURRENT ASSETS (Bn. VND)",
            "Cash and cash equivalents": "Cash and cash equivalents (Bn. VND)",
            "Short-term investments": "Short-term investments (Bn. VND)",
            "Short-term receivables": "Accounts receivable (Bn. VND)",
            "Net inventories": "Net Inventories",
            "Other current assets": "Other current assets",
            "LONG-TERM ASSETS": "LONG-TERM ASSETS (Bn. VND)",
            "Long-term receivables": "Long-term trade receivables (Bn. VND)",
            "Fixed assets": "Fixed assets (Bn. VND)",
            "Investment properties": "Investment in properties",
            "Long-term assets in progress": "Long-term assets in progress",
            "Long-term investments": "Long-term investments (Bn. VND)",
            "Other long-term assets": "Other non-current assets",
            "TOTAL RESOURCES": "TOTAL RESOURCES (Bn. VND)",
            "TOTAL LIABILITIES": "LIABILITIES (Bn. VND)",
            "Current liabilities": "Current liabilities (Bn. VND)",
            "Short Term Debt": "Short-term borrowings (Bn. VND)",
            "Long-term liabilities": "Long-term liabilities (Bn. VND)",
            "Long Term Debt": "Long-term borrowings (Bn. VND)",
            "OWNER'S EQUITY": "OWNER'S EQUITY(Bn.VND)",
            "Capital and reserves": "Capital and reserves (Bn. VND)",
            "Share Capital": "Paid-in capital (Bn. VND)",
            "Other Owners' Capital": "Other Reserves",
            "Undistributed earnings": "Undistributed earnings (Bn. VND)",
            "Minority interests": "MINORITY INTERESTS",
            "Budget sources and other funds": "Budget sources and other funds",
        }

    # Apply balance sheet mappings
    for new_name, old_name in balance_mapping.items():
        transformed_balance[new_name] = safe_get(balance_df, old_name)

    # === TRANSFORM CASH FLOW ===
    cash_flow_df = cash_flow.copy()
    transformed_cash_flow = pd.DataFrame()
    if not cash_flow_df.empty:
        transformed_cash_flow.index = cash_flow_df.index

    # Cash flow mapping (same for banks and non-banks)
    cash_flow_mapping = {
        "Year": "yearReport",
        "Quarter": "lengthReport" if period == "quarter" else None,
        "Operating cash flow": "Net cash inflows/outflows from operating activities",
        "Investing cash flow": "Net Cash Flows from Investing Activities",
        "Financing cash flow": "Cash flows from financial activities",
        "Ending cash position": "Cash and Cash Equivalents at the end of period",
        "Dividends paid": "Dividends paid",
        "Share repurchase": "Payments for share repurchases",
        "Capital expenditure": "Purchase of fixed assets",
    }

    for new_name, old_name in cash_flow_mapping.items():
        transformed_cash_flow[new_name] = safe_get(cash_flow_df, old_name)

    # Calculate Free Cash Flow
    operating_cf = transformed_cash_flow.get(
        "Operating cash flow", pd.Series(dtype=float)
    )
    capex = transformed_cash_flow.get("Capital expenditure", pd.Series(dtype=float))
    if not operating_cf.isna().all() and not capex.isna().all():
        transformed_cash_flow["Free cash flow"] = operating_cf.fillna(0) + capex.fillna(
            0
        )
    else:
        transformed_cash_flow["Free cash flow"] = pd.NA

    # === TRANSFORM KEY RATIOS (CATEGORIZED) - FIXED FOR MULTIINDEX ===
    ratios_index = key_ratios.index if not key_ratios.empty else []

    # Initialize categorized ratio DataFrames
    per_share = pd.DataFrame(index=ratios_index)
    growth_rate = pd.DataFrame(index=ratios_index)
    profitability = pd.DataFrame(index=ratios_index)
    valuation = pd.DataFrame(index=ratios_index)
    leverage_liquidity = pd.DataFrame(index=ratios_index)
    efficiency = pd.DataFrame(index=ratios_index)

    if is_bank:
        # === BANK RATIOS - FIXED FOR MULTIINDEX ===

        # Add time period columns based on period type
        per_share["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        growth_rate["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        profitability["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        valuation["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        leverage_liquidity["Year"] = safe_get_multiindex(
            key_ratios, "Meta", "yearReport"
        )
        efficiency["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")

        if period == "quarter":
            per_share["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            growth_rate["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            profitability["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            valuation["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            leverage_liquidity["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            efficiency["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )

        # Per Share Value
        per_share["Earnings"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "EPS (VND)"
        )

        outstanding_shares = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "Outstanding Share (Mil. Shares)"
        )
        operating_cf = safe_get(transformed_cash_flow, "Operating cash flow")
        capex = safe_get(transformed_cash_flow, "Capital expenditure")
        dividends_paid = safe_get(transformed_cash_flow, "Dividends paid")

        # Free Cash Flow per share
        if not operating_cf.isna().all() and not outstanding_shares.isna().all():
            fcf_total = operating_cf.fillna(0) + capex.fillna(0)
            per_share["Free Cash Flow"] = fcf_total / outstanding_shares.replace(
                0, pd.NA
            )
        else:
            per_share["Free Cash Flow"] = pd.NA

        # Dividend per share
        if not dividends_paid.isna().all() and not outstanding_shares.isna().all():
            per_share["Dividend"] = (-dividends_paid) / outstanding_shares.replace(
                0, pd.NA
            )
        else:
            per_share["Dividend"] = pd.NA

        per_share["Book Value"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "BVPS (VND)"
        )

        # Growth Rates
        growth_rate["Earnings YoY"] = calculate_yoy_growth(per_share["Earnings"])
        growth_rate["Free Cash Flow YoY"] = calculate_yoy_growth(
            per_share["Free Cash Flow"]
        )
        growth_rate["Dividend YoY"] = calculate_yoy_growth(per_share["Dividend"])
        growth_rate["Book Value YoY"] = calculate_yoy_growth(per_share["Book Value"])

        # Profitability
        profitability["Net Margin"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "Net Profit Margin (%)"
        )
        profitability["ROE"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "ROE (%)"
        )

        # Valuation
        valuation["P/E"] = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "P/E")
        valuation["P/S"] = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "P/S")
        valuation["P/B"] = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "P/B")
        valuation["P/Cash Flow"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "P/Cash Flow"
        )

        # Leverage & Liquidity
        liabilities = safe_get(transformed_balance, "Liabilities")
        equity = safe_get(transformed_balance, "Shareholders' Equity")
        if not liabilities.isna().all() and not equity.isna().all():
            leverage_liquidity["Debt/Equity"] = liabilities / equity.replace(0, pd.NA)
        else:
            leverage_liquidity["Debt/Equity"] = pd.NA

        leverage_liquidity["Financial Leverage"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu thanh khoản", "Financial Leverage"
        )

        # Efficiency
        efficiency["ROA"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "ROA (%)"
        )

        attributable_profit = safe_get(
            transformed_income, "Attributable to parent company"
        )
        if not dividends_paid.isna().all() and not attributable_profit.isna().all():
            efficiency["Dividend Payout %"] = (
                -dividends_paid / attributable_profit.replace(0, pd.NA)
            ) * 100
        else:
            efficiency["Dividend Payout %"] = pd.NA

    else:
        # === NON-BANK RATIOS - FIXED FOR MULTIINDEX ===

        # Add time period columns based on period type
        per_share["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        growth_rate["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        profitability["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        valuation["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")
        leverage_liquidity["Year"] = safe_get_multiindex(
            key_ratios, "Meta", "yearReport"
        )
        efficiency["Year"] = safe_get_multiindex(key_ratios, "Meta", "yearReport")

        if period == "quarter":
            per_share["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            growth_rate["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            profitability["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            valuation["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            leverage_liquidity["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )
            efficiency["Quarter"] = safe_get_multiindex(
                key_ratios, "Meta", "lengthReport"
            )

        # Per Share Value
        net_sales = safe_get(transformed_income, "Net sales")
        outstanding_shares = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "Outstanding Share (Mil. Shares)"
        )
        operating_cf = safe_get(transformed_cash_flow, "Operating cash flow")
        capex = safe_get(transformed_cash_flow, "Capital expenditure")
        dividends_paid = safe_get(transformed_cash_flow, "Dividends paid")

        # Revenue per share
        if not net_sales.isna().all() and not outstanding_shares.isna().all():
            per_share["Revenues"] = net_sales / outstanding_shares.replace(0, pd.NA)
        else:
            per_share["Revenues"] = pd.NA

        per_share["Earnings"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "EPS (VND)"
        )

        # Free Cash Flow per share
        if not operating_cf.isna().all() and not outstanding_shares.isna().all():
            fcf_total = operating_cf.fillna(0) + capex.fillna(0)
            per_share["Free Cash Flow"] = fcf_total / outstanding_shares.replace(
                0, pd.NA
            )
        else:
            per_share["Free Cash Flow"] = pd.NA

        # Dividend per share
        if not dividends_paid.isna().all() and not outstanding_shares.isna().all():
            per_share["Dividend"] = (-dividends_paid) / outstanding_shares.replace(
                0, pd.NA
            )
        else:
            per_share["Dividend"] = pd.NA

        per_share["Book Value"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "BVPS (VND)"
        )

        # Growth Rates
        growth_rate["Revenues YoY"] = calculate_yoy_growth(per_share["Revenues"])
        growth_rate["Earnings YoY"] = calculate_yoy_growth(per_share["Earnings"])
        growth_rate["Free Cash Flow YoY"] = calculate_yoy_growth(
            per_share["Free Cash Flow"]
        )
        growth_rate["Dividend YoY"] = calculate_yoy_growth(per_share["Dividend"])
        growth_rate["Book Value YoY"] = calculate_yoy_growth(per_share["Book Value"])

        # Profitability
        profitability["Gross Margin"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "Gross Profit Margin (%)"
        )

        operating_profit = safe_get(transformed_income, "Operating income")
        if not operating_profit.isna().all() and not net_sales.isna().all():
            profitability["Operating Margin"] = (
                operating_profit / net_sales.replace(0, pd.NA)
            ) * 100
        else:
            profitability["Operating Margin"] = pd.NA

        profitability["Net Margin"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "Net Profit Margin (%)"
        )
        profitability["ROE"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "ROE (%)"
        )
        profitability["ROIC"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "ROIC (%)"
        )

        # ROCE calculation
        ebit = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "EBIT (Bn. VND)"
        )
        total_assets = safe_get(transformed_balance, "TOTAL ASSETS")
        current_liabilities = safe_get(transformed_balance, "Current liabilities")
        if (
            not ebit.isna().all()
            and not total_assets.isna().all()
            and not current_liabilities.isna().all()
        ):
            employed_capital = total_assets - current_liabilities
            profitability["ROCE"] = (ebit / employed_capital.replace(0, pd.NA)) * 100
        else:
            profitability["ROCE"] = pd.NA

        # Margin calculations
        ebitda = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "EBITDA (Bn. VND)"
        )
        if not ebitda.isna().all() and not net_sales.isna().all():
            profitability["EBITDA Margin"] = (
                ebitda / net_sales.replace(0, pd.NA)
            ) * 100
        else:
            profitability["EBITDA Margin"] = pd.NA

        profitability["EBIT Margin"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "EBIT Margin (%)"
        )

        # Valuation
        valuation["P/E"] = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "P/E")
        valuation["P/S"] = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "P/S")
        valuation["P/B"] = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "P/B")
        valuation["P/Cash Flow"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu định giá", "P/Cash Flow"
        )

        # EV calculations
        ev_ebitda = safe_get_multiindex(key_ratios, "Chỉ tiêu định giá", "EV/EBITDA")
        if not ev_ebitda.isna().all() and not ebitda.isna().all():
            valuation["EV"] = ev_ebitda * ebitda
        else:
            valuation["EV"] = pd.NA

        valuation["EV/EBITDA"] = ev_ebitda

        if not valuation["EV"].isna().all() and not net_sales.isna().all():
            valuation["EV/Revenue"] = valuation["EV"] / net_sales.replace(0, pd.NA)
        else:
            valuation["EV/Revenue"] = pd.NA

        # Leverage & Liquidity
        leverage_liquidity["Debt/Equity"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu cơ cấu nguồn vốn", "Debt/Equity"
        )

        # Debt to EBITDA
        lt_debt = safe_get(transformed_balance, "Long Term Debt")
        st_debt = safe_get(transformed_balance, "Short Term Debt")
        total_debt = lt_debt.fillna(0) + st_debt.fillna(0)
        if not total_debt.isna().all() and not ebitda.isna().all():
            leverage_liquidity["Debt to EBITDA"] = total_debt / ebitda.replace(0, pd.NA)
        else:
            leverage_liquidity["Debt to EBITDA"] = pd.NA

        leverage_liquidity["Short and Long Term Borrowings to Equity"] = (
            safe_get_multiindex(
                key_ratios, "Chỉ tiêu cơ cấu nguồn vốn", "(ST+LT borrowings)/Equity"
            )
        )
        leverage_liquidity["Financial Leverage"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu thanh khoản", "Financial Leverage"
        )
        leverage_liquidity["Quick Ratio"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu thanh khoản", "Quick Ratio"
        )
        leverage_liquidity["Current Ratio"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu thanh khoản", "Current Ratio"
        )
        leverage_liquidity["Cash Ratio"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu thanh khoản", "Cash Ratio"
        )
        leverage_liquidity["Interest Coverage"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu thanh khoản", "Interest Coverage"
        )

        # Efficiency
        efficiency["Asset Turnover"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu hiệu quả hoạt động", "Asset Turnover"
        )
        efficiency["Inventory Turnover"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu hiệu quả hoạt động", "Inventory Turnover"
        )
        efficiency["ROA"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu khả năng sinh lợi", "ROA (%)"
        )

        # Dividend Payout %
        attributable_profit = safe_get(
            transformed_income, "Attributable to parent company"
        )
        if not dividends_paid.isna().all() and not attributable_profit.isna().all():
            efficiency["Dividend Payout %"] = (
                -dividends_paid / attributable_profit.replace(0, pd.NA)
            ) * 100
        else:
            efficiency["Dividend Payout %"] = pd.NA

        efficiency["Cash Conversion Cycle"] = safe_get_multiindex(
            key_ratios, "Chỉ tiêu hiệu quả hoạt động", "Cash Cycle"
        )

    # === RETURN COMPLETE RESULTS ===
    return {
        # Original data
        "ticker": ticker_symbol,
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "key_ratios": key_ratios,
        # Transformed statements
        "transformed_income_statement": transformed_income,
        "transformed_balance_sheet": transformed_balance,
        "transformed_cash_flow": transformed_cash_flow,
        # Categorized ratios
        "categorized_ratios": {
            "Per Share Value": per_share,
            "Growth Rate": growth_rate,
            "Profitability": profitability,
            "Valuation": valuation,
            "Leverage & Liquidity": leverage_liquidity,
            "Efficiency": efficiency,
        },
        # Metadata
        "is_bank": is_bank,
    }