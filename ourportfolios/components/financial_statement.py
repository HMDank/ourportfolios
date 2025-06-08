import reflex as rx
import io
import csv


class State(rx.State):
    expanded_table: int = -1

    @rx.event
    def expand(self, idx: int):
        self.expanded_table = idx

    @rx.event
    def handle_dialog_open(self, value: bool):
        if not value:
            self.expanded_table = -1

    @rx.event
    def close(self):
        self.expanded_table = -1

    @rx.event
    def download_table_csv(self, data: list, idx: int):
        if not data:
            return
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        csv_data = output.getvalue()
        output.close()
        return rx.download(
            data=csv_data,
            filename=f"table_{idx}.csv"
        )


def financial_statements(df_list):
    return rx.vstack(
        *[rx.box(preview_table(tbl, i), expanded_dialog(tbl, i), style={"minWidth": "0"})
          for i, tbl in enumerate(df_list)],
        spacing='4',
        style={"minWidth": "0"}
    )


def preview_table(data, idx):
    title = ["Income Statement", "Balance Sheet", "Cash Flow"][idx]
    return rx.cond(
        data.length() > 0,
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(title, weight="bold", size="8"),
                    rx.hstack(
                        rx.icon("maximize", on_click=lambda: State.expand(idx), style={
                            "cursor": "pointer",
                            "userSelect": "none",
                            "color": rx.color("accent", 10),
                            "_hover": {"color": rx.color("accent", 7)},
                        }),
                        rx.icon("download", on_click=lambda: State.download_table_csv(data, idx), size=1, style={
                            "cursor": "pointer",
                            "userSelect": "none",
                            "color": rx.color("accent", 10),
                            "_hover": {"color": rx.color("accent", 7)},
                        }),
                        spacing="2",
                    ),
                    width="12em",
                    flex_shrink="0",
                ),
                # Use rx.scroll_area here:
                rx.scroll_area(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.foreach(
                                    data[0].keys(),
                                    lambda h: rx.table.column_header_cell(h)
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
                                            rx.text(
                                                row[h]) if row[h] is not None else rx.text("")
                                        )
                                    )
                                )
                            )
                        ),
                        size="1",
                        variant="surface",
                        style={
                            "minWidth": "max-content",
                            "width": "auto",
                            "display": "table",
                        }
                    ),
                    # Control scrolling here
                    scrollbars="horizontal",
                    type="always",
                    style={
                        "height": "auto",
                        "width": "100%",
                        "maxWidth": "600px",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "6px",
                        "position": "relative",
                        "display": "block",
                    }
                ),
                spacing="4",
                style={
                    "width": "100%",
                    "alignItems": "flex-start"
                }
            ),
            width="100%",
        ),
        rx.text("No data available")
    )


def expanded_dialog(data, idx):
    return rx.cond(
        State.expanded_table == idx,
        rx.dialog.root(
            rx.dialog.trigger(
                rx.button("hidden", style={"display": "none"})
            ),
            rx.dialog.content(
                rx.vstack(
                    rx.hstack(
                        rx.dialog.close(
                            rx.text(
                                rx.icon("x"),
                                on_click=State.close,
                                style={
                                    "cursor": "pointer",
                                    "userSelect": "none",
                                    "color": rx.color("accent", 10),
                                    "_hover": {
                                        "color": rx.color("accent", 7),
                                    },
                                },
                            ),
                        ),
                        rx.text(
                            ["Income Statement", "Balance Sheet", "Cash Flow"][idx],
                            weight="bold",
                            size="6",
                        ),
                        width="100%",
                        padding_bottom="1rem",
                        align="center",
                        justify="between",
                    ),
                    rx.center(
                        rx.scroll_area(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.foreach(
                                            data[0].keys(),
                                            lambda h: rx.table.column_header_cell(
                                                h)
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
                                                        row[h] != None,
                                                        rx.text(row[h]),
                                                        rx.text("")
                                                    )
                                                )
                                            )
                                        )
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
                        width="100%"
                    ),

                    spacing="4",  # Space between elements in vstack
                    align="center",  # Center align the vstack contents
                    width="100%",
                    height="100%"
                ),
                max_width="90vw",
                style={
                    "height": "80vh",
                    "padding": "1.5rem"  # Add padding to the entire dialog content
                },
            ),
            open=True,
            on_open_change=State.handle_dialog_open,
        ),
        None
    )
