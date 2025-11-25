"""Financial statement UI component for displaying income statement, balance sheet, and cash flow."""

import reflex as rx
from ..state import FinancialStatementState
from .dialog import common_dialog

titles = ["Income\nStatement", "Balance\nSheet", "Cash\nFlow"]


def financial_statements(df_list):
    return rx.vstack(
        *[
            rx.box(
                preview_table(tbl, i), expanded_dialog(tbl, i), style={"minWidth": "0"}
            )
            for i, tbl in enumerate(df_list)
        ],
        spacing="4",
        style={"minWidth": "0"},
    )


def preview_table(data, idx):
    title = titles[idx]
    return rx.cond(
        data.length() > 0,
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        title,
                        weight="medium",
                        size="7",
                        white_space="pre-line",
                    ),
                    rx.hstack(
                        rx.icon(
                            "maximize",
                            on_click=lambda: FinancialStatementState.expand(idx),
                            style={
                                "cursor": "pointer",
                                "userSelect": "none",
                                "color": rx.color("accent", 10),
                                "_hover": {"color": rx.color("accent", 7)},
                            },
                        ),
                        rx.icon(
                            "download",
                            on_click=lambda: FinancialStatementState.download_table_csv(data, idx),
                            style={
                                "cursor": "pointer",
                                "userSelect": "none",
                                "color": rx.color("accent", 10),
                                "_hover": {"color": rx.color("accent", 7)},
                            },
                        ),
                        spacing="2",
                    ),
                    width="12em",
                    flex_shrink="0",
                    justify="center",
                    padding_left="1em",
                ),
                # Use rx.scroll_area here:
                rx.scroll_area(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.foreach(
                                    data[0].keys(),
                                    lambda h: rx.table.column_header_cell(h),
                                )
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                data[:5],
                                lambda row: rx.table.row(
                                    rx.foreach(
                                        data[0].keys(),
                                        lambda h: rx.table.cell(
                                            rx.text(row[h])
                                            if row[h] is not None
                                            else rx.text("")
                                        ),
                                    )
                                ),
                            )
                        ),
                        size="1",
                        variant="surface",
                        style={
                            "minWidth": "max-content",
                            "width": "auto",
                            "display": "table",
                        },
                    ),
                    # Control scrolling here
                    scrollbars="horizontal",
                    type="hover",
                    style={
                        "height": "auto",
                        "maxWidth": "43em",
                        "position": "relative",
                        "display": "block",
                    },
                ),
                spacing="4",
                style={"width": "100%", "alignItems": "center"},
            ),
            width="100%",
        ),
        rx.text("No data available"),
    )


def expanded_dialog(data, idx):
    content = rx.center(
        rx.scroll_area(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            data[0].keys(),
                            lambda h: rx.table.column_header_cell(h),
                        )
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        data,
                        lambda row: rx.table.row(
                            rx.foreach(
                                data[0].keys(),
                                lambda h: rx.table.cell(
                                    rx.cond(
                                        row[h] is not None,
                                        rx.text(row[h]),
                                        rx.text(""),
                                    )
                                ),
                            )
                        ),
                    )
                ),
                size="2",
                variant="surface",
                style={"fontSize": "12px"},
            ),
            style={
                "height": "67vh",
                "width": "90vw",
            },
            scrollbars="both",
        ),
        width="100%",
    )
    
    return common_dialog(
        content=content,
        is_open=FinancialStatementState.expanded_table == idx,
        on_close=FinancialStatementState.close,
        on_open_change=FinancialStatementState.handle_dialog_open,
        width="90vw",
        height="80vh",
        max_width="90vw",
        padding="1.5rem",
        title=["Income Statement", "Balance Sheet", "Cash Flow"][idx],
    )
