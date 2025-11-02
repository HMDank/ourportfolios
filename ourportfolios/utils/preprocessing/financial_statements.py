from vnstock import Vnstock
import pandas as pd
import asyncio


async def get_transformed_dataframes(ticker_symbol, period="year"):
    def calculate_yoy_growth(series):
        if len(series) < 2:
            return pd.Series(dtype=float, index=series.index)
        series_sorted = series.sort_index()
        return series_sorted.pct_change() * 100

    income_statement, balance_sheet, cash_flow, key_ratios_raw = await asyncio.gather(
        asyncio.to_thread(
            lambda: Vnstock()
            .stock(symbol=ticker_symbol, source="VCI")
            .finance.income_statement(period=period, lang="en")
        ),
        asyncio.to_thread(
            lambda: Vnstock()
            .stock(symbol=ticker_symbol, source="VCI")
            .finance.balance_sheet(period=period, lang="en")
        ),
        asyncio.to_thread(
            lambda: Vnstock()
            .stock(symbol=ticker_symbol, source="VCI")
            .finance.cash_flow(period=period, lang="en")
        ),
        asyncio.to_thread(
            lambda: Vnstock()
            .stock(symbol=ticker_symbol, source="VCI")
            .finance.ratio(period=period, lang="en")
        ),
    )

    if isinstance(key_ratios_raw.columns, pd.MultiIndex):
        key_ratios = key_ratios_raw.copy()
        key_ratios.columns = [col[1] for col in key_ratios_raw.columns]
    else:
        key_ratios = key_ratios_raw

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
        if old_name and old_name in income_df.columns:
            transformed_income[new_name] = income_df[old_name]
        else:
            transformed_income[new_name] = pd.NA

    # Add ratio-based columns AFTER the mappings (at the end of the table)
    if is_bank:
        # Add ratio-based columns for banks using regular column access
        transformed_income["EPS"] = key_ratios["EPS (VND)"]
        transformed_income["Outstanding Share"] = key_ratios[
            "Outstanding Share (Mil. Shares)"
        ]
    else:
        # Add ratio-based columns for non-banks using regular column access
        transformed_income["EPS"] = key_ratios["EPS (VND)"]
        transformed_income["Outstanding Share"] = key_ratios[
            "Outstanding Share (Mil. Shares)"
        ]
        transformed_income["EBITDA"] = key_ratios["EBITDA (Bn. VND)"]
        transformed_income["EBIT"] = key_ratios["EBIT (Bn. VND)"]

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
        if old_name and old_name in balance_df.columns:
            transformed_balance[new_name] = balance_df[old_name]
        else:
            transformed_balance[new_name] = pd.NA

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
        if old_name and old_name in cash_flow_df.columns:
            transformed_cash_flow[new_name] = cash_flow_df[old_name]
        else:
            transformed_cash_flow[new_name] = pd.NA

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

    # === TRANSFORM KEY RATIOS (CATEGORIZED) ===
    ratios_index = key_ratios.index if not key_ratios.empty else []

    # Initialize categorized ratio DataFrames
    per_share = pd.DataFrame(index=ratios_index)
    growth_rate = pd.DataFrame(index=ratios_index)
    profitability = pd.DataFrame(index=ratios_index)
    valuation = pd.DataFrame(index=ratios_index)
    leverage_liquidity = pd.DataFrame(index=ratios_index)
    efficiency = pd.DataFrame(index=ratios_index)

    if is_bank:
        # === BANK RATIOS - USING FLATTENED COLUMNS ===

        # Add time period columns based on period type
        per_share["Year"] = key_ratios["yearReport"]
        growth_rate["Year"] = key_ratios["yearReport"]
        profitability["Year"] = key_ratios["yearReport"]
        valuation["Year"] = key_ratios["yearReport"]
        leverage_liquidity["Year"] = key_ratios["yearReport"]
        efficiency["Year"] = key_ratios["yearReport"]

        if period == "quarter":
            per_share["Quarter"] = key_ratios["lengthReport"]
            growth_rate["Quarter"] = key_ratios["lengthReport"]
            profitability["Quarter"] = key_ratios["lengthReport"]
            valuation["Quarter"] = key_ratios["lengthReport"]
            leverage_liquidity["Quarter"] = key_ratios["lengthReport"]
            efficiency["Quarter"] = key_ratios["lengthReport"]

        # Per Share Value
        per_share["Earnings"] = key_ratios["EPS (VND)"]

        outstanding_shares = key_ratios["Outstanding Share (Mil. Shares)"]
        operating_cf = (
            transformed_cash_flow["Operating cash flow"]
            if "Operating cash flow" in transformed_cash_flow.columns
            else pd.Series(dtype=float)
        )
        capex = (
            transformed_cash_flow["Capital expenditure"]
            if "Capital expenditure" in transformed_cash_flow.columns
            else pd.Series(dtype=float)
        )
        dividends_paid = (
            transformed_cash_flow["Dividends paid"]
            if "Dividends paid" in transformed_cash_flow.columns
            else pd.Series(dtype=float)
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

        per_share["Book Value"] = key_ratios["BVPS (VND)"]

        # Growth Rates
        growth_rate["Earnings YoY"] = calculate_yoy_growth(per_share["Earnings"])
        growth_rate["Free Cash Flow YoY"] = calculate_yoy_growth(
            per_share["Free Cash Flow"]
        )
        growth_rate["Dividend YoY"] = calculate_yoy_growth(per_share["Dividend"])
        growth_rate["Book Value YoY"] = calculate_yoy_growth(per_share["Book Value"])

        # Profitability
        profitability["Net Margin"] = key_ratios["Net Profit Margin (%)"]
        profitability["ROE"] = key_ratios["ROE (%)"]

        # Valuation
        valuation["P/E"] = key_ratios["P/E"]
        valuation["P/S"] = key_ratios["P/S"]
        valuation["P/B"] = key_ratios["P/B"]
        valuation["P/Cash Flow"] = key_ratios["P/Cash Flow"]

        # Leverage & Liquidity
        liabilities = (
            transformed_balance["Liabilities"]
            if "Liabilities" in transformed_balance.columns
            else pd.Series(dtype=float)
        )
        equity = (
            transformed_balance["Shareholders' Equity"]
            if "Shareholders' Equity" in transformed_balance.columns
            else pd.Series(dtype=float)
        )
        if not liabilities.isna().all() and not equity.isna().all():
            leverage_liquidity["Debt/Equity"] = liabilities / equity.replace(0, pd.NA)
        else:
            leverage_liquidity["Debt/Equity"] = pd.NA

        leverage_liquidity["Financial Leverage"] = key_ratios["Financial Leverage"]

        # Efficiency
        efficiency["ROA"] = key_ratios["ROA (%)"]

        attributable_profit = (
            transformed_income["Attributable to parent company"]
            if "Attributable to parent company" in transformed_income.columns
            else pd.Series(dtype=float)
        )
        if not dividends_paid.isna().all() and not attributable_profit.isna().all():
            efficiency["Dividend Payout %"] = (
                -dividends_paid / attributable_profit.replace(0, pd.NA)
            ) * 100
        else:
            efficiency["Dividend Payout %"] = pd.NA

    else:
        # === NON-BANK RATIOS - USING FLATTENED COLUMNS ===

        # Add time period columns based on period type
        per_share["Year"] = key_ratios["yearReport"]
        growth_rate["Year"] = key_ratios["yearReport"]
        profitability["Year"] = key_ratios["yearReport"]
        valuation["Year"] = key_ratios["yearReport"]
        leverage_liquidity["Year"] = key_ratios["yearReport"]
        efficiency["Year"] = key_ratios["yearReport"]

        if period == "quarter":
            per_share["Quarter"] = key_ratios["lengthReport"]
            growth_rate["Quarter"] = key_ratios["lengthReport"]
            profitability["Quarter"] = key_ratios["lengthReport"]
            valuation["Quarter"] = key_ratios["lengthReport"]
            leverage_liquidity["Quarter"] = key_ratios["lengthReport"]
            efficiency["Quarter"] = key_ratios["lengthReport"]

        # Per Share Value
        net_sales = (
            transformed_income["Net sales"]
            if "Net sales" in transformed_income.columns
            else pd.Series(dtype=float)
        )
        outstanding_shares = key_ratios["Outstanding Share (Mil. Shares)"]
        operating_cf = (
            transformed_cash_flow["Operating cash flow"]
            if "Operating cash flow" in transformed_cash_flow.columns
            else pd.Series(dtype=float)
        )
        capex = (
            transformed_cash_flow["Capital expenditure"]
            if "Capital expenditure" in transformed_cash_flow.columns
            else pd.Series(dtype=float)
        )
        dividends_paid = (
            transformed_cash_flow["Dividends paid"]
            if "Dividends paid" in transformed_cash_flow.columns
            else pd.Series(dtype=float)
        )

        # Revenue per share
        if not net_sales.isna().all() and not outstanding_shares.isna().all():
            per_share["Revenues"] = net_sales / outstanding_shares.replace(0, pd.NA)
        else:
            per_share["Revenues"] = pd.NA

        per_share["Earnings"] = key_ratios["EPS (VND)"]

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

        per_share["Book Value"] = key_ratios["BVPS (VND)"]

        # Growth Rates
        growth_rate["Revenues YoY"] = calculate_yoy_growth(per_share["Revenues"])
        growth_rate["Earnings YoY"] = calculate_yoy_growth(per_share["Earnings"])
        growth_rate["Free Cash Flow YoY"] = calculate_yoy_growth(
            per_share["Free Cash Flow"]
        )
        growth_rate["Dividend YoY"] = calculate_yoy_growth(per_share["Dividend"])
        growth_rate["Book Value YoY"] = calculate_yoy_growth(per_share["Book Value"])

        # Profitability
        profitability["Gross Margin"] = key_ratios["Gross Profit Margin (%)"]

        operating_profit = (
            transformed_income["Operating income"]
            if "Operating income" in transformed_income.columns
            else pd.Series(dtype=float)
        )
        if not operating_profit.isna().all() and not net_sales.isna().all():
            profitability["Operating Margin"] = (
                operating_profit / net_sales.replace(0, pd.NA)
            ) * 100
        else:
            profitability["Operating Margin"] = pd.NA

        profitability["Net Margin"] = key_ratios["Net Profit Margin (%)"]
        profitability["ROE"] = key_ratios["ROE (%)"]
        profitability["ROIC"] = key_ratios["ROIC (%)"]

        # ROCE calculation
        ebit = key_ratios["EBIT (Bn. VND)"]
        total_assets = (
            transformed_balance["TOTAL ASSETS"]
            if "TOTAL ASSETS" in transformed_balance.columns
            else pd.Series(dtype=float)
        )
        current_liabilities = (
            transformed_balance["Current liabilities"]
            if "Current liabilities" in transformed_balance.columns
            else pd.Series(dtype=float)
        )
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
        ebitda = key_ratios["EBITDA (Bn. VND)"]
        if not ebitda.isna().all() and not net_sales.isna().all():
            profitability["EBITDA Margin"] = (
                ebitda / net_sales.replace(0, pd.NA)
            ) * 100
        else:
            profitability["EBITDA Margin"] = pd.NA

        profitability["EBIT Margin"] = key_ratios["EBIT Margin (%)"]

        # Valuation
        valuation["P/E"] = key_ratios["P/E"]
        valuation["P/S"] = key_ratios["P/S"]
        valuation["P/B"] = key_ratios["P/B"]
        valuation["P/Cash Flow"] = key_ratios["P/Cash Flow"]

        # EV calculations
        ev_ebitda = key_ratios["EV/EBITDA"]
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
        leverage_liquidity["Debt/Equity"] = key_ratios["Debt/Equity"]

        # Debt to EBITDA
        lt_debt = (
            transformed_balance["Long Term Debt"]
            if "Long Term Debt" in transformed_balance.columns
            else pd.Series(dtype=float)
        )
        st_debt = (
            transformed_balance["Short Term Debt"]
            if "Short Term Debt" in transformed_balance.columns
            else pd.Series(dtype=float)
        )
        total_debt = lt_debt.fillna(0) + st_debt.fillna(0)
        if not total_debt.isna().all() and not ebitda.isna().all():
            leverage_liquidity["Debt to EBITDA"] = total_debt / ebitda.replace(0, pd.NA)
        else:
            leverage_liquidity["Debt to EBITDA"] = pd.NA

        leverage_liquidity["Short and Long Term Borrowings to Equity"] = key_ratios[
            "(ST+LT borrowings)/Equity"
        ]
        leverage_liquidity["Financial Leverage"] = key_ratios["Financial Leverage"]
        leverage_liquidity["Quick Ratio"] = key_ratios["Quick Ratio"]
        leverage_liquidity["Current Ratio"] = key_ratios["Current Ratio"]
        leverage_liquidity["Cash Ratio"] = key_ratios["Cash Ratio"]
        leverage_liquidity["Interest Coverage"] = key_ratios["Interest Coverage"]

        # Efficiency
        efficiency["Asset Turnover"] = key_ratios["Asset Turnover"]
        # Inventory Turnover is optional (not available for all companies)
        if "Inventory Turnover" in key_ratios.columns:
            efficiency["Inventory Turnover"] = key_ratios["Inventory Turnover"]
        efficiency["ROA"] = key_ratios["ROA (%)"]

        # Dividend Payout %
        attributable_profit = (
            transformed_income["Attributable to parent company"]
            if "Attributable to parent company" in transformed_income.columns
            else pd.Series(dtype=float)
        )
        if not dividends_paid.isna().all() and not attributable_profit.isna().all():
            efficiency["Dividend Payout %"] = (
                -dividends_paid / attributable_profit.replace(0, pd.NA)
            ) * 100
        else:
            efficiency["Dividend Payout %"] = pd.NA

        efficiency["Cash Conversion Cycle"] = key_ratios["Cash Cycle"]

    return {
        # Transformed statements
        "transformed_income_statement": transformed_income.to_dict(orient="records"),
        "transformed_balance_sheet": transformed_balance.to_dict(orient="records"),
        "transformed_cash_flow": transformed_cash_flow.to_dict(orient="records"),
        # Categorized ratios
        "categorized_ratios": {
            "Per Share Value": per_share.to_dict(orient="records"),
            "Growth Rate": growth_rate.to_dict(orient="records"),
            "Profitability": profitability.to_dict(orient="records"),
            "Valuation": valuation.to_dict(orient="records"),
            "Leverage & Liquidity": leverage_liquidity.to_dict(orient="records"),
            "Efficiency": efficiency.to_dict(orient="records"),
        },
    }


def format_quarter_data(data_list):
    processed_data = []

    for item in data_list:
        processed_item = item.copy()

        year = item.get("Year", "")
        quarter = item.get("Quarter", "")

        if year and quarter:
            quarter_str = f"Q{quarter} {year}"
        else:
            quarter_str = f"{year}" if year else ""

        processed_item["formatted_quarter"] = quarter_str
        processed_item.pop("Quarter", None)
        processed_data.append(processed_item)

    return processed_data
