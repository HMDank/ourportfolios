import reflex as rx

config = rx.Config(
    app_name="ourportfolios",
    plugins=[
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.sitemap.SitemapPlugin(),
        ],
)
