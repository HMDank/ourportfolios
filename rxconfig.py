import reflex as rx

config = rx.Config(
    app_name="ourportfolios",
    plugins=[rx.plugins.TailwindV3Plugin()],
    db_url='postgresql://neondb_owner:npg_VKsJaR5Cj8kh@ep-purple-shadow-a2j94ffd-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require',
)
