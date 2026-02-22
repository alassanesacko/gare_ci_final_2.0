from django.db import migrations, models
import django.db.models.deletion


def ensure_gareci_admin_schema(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "sqlite":
        return

    with conn.cursor() as cursor:
        def table_exists(name):
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                [name],
            )
            return cursor.fetchone() is not None

        def columns(table):
            cursor.execute(f"PRAGMA table_info({table})")
            return {row[1] for row in cursor.fetchall()}

        def add_col(table, ddl):
            col_name = ddl.split()[0]
            if col_name not in columns(table):
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

        if table_exists("gareci_admin_conducteur"):
            add_col("gareci_admin_conducteur", "cin varchar(50)")
            add_col("gareci_admin_conducteur", "telephone varchar(50)")
            add_col("gareci_admin_conducteur", "numero_permis varchar(100)")
            add_col("gareci_admin_conducteur", "type_permis varchar(3)")
            add_col("gareci_admin_conducteur", "date_expiration_permis date")
            add_col("gareci_admin_conducteur", "statut varchar(10) DEFAULT 'ACTIF'")
            add_col("gareci_admin_conducteur", "photo varchar(100)")
            cursor.execute(
                "UPDATE gareci_admin_conducteur "
                "SET telephone = COALESCE(telephone, contact)"
            )
            cursor.execute(
                "UPDATE gareci_admin_conducteur "
                "SET numero_permis = COALESCE(numero_permis, permis)"
            )
            cursor.execute(
                "UPDATE gareci_admin_conducteur "
                "SET statut = COALESCE(statut, CASE WHEN actif = 1 THEN 'ACTIF' ELSE 'SUSPENDU' END)"
            )
            cursor.execute(
                "UPDATE gareci_admin_conducteur "
                "SET cin = COALESCE(cin, 'CIN-' || id)"
            )
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS gareci_admin_conducteur_cin_uniq "
                "ON gareci_admin_conducteur(cin)"
            )

        if not table_exists("gareci_admin_affectationconducteur"):
            cursor.execute(
                """
                CREATE TABLE gareci_admin_affectationconducteur (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role varchar(12) NOT NULL DEFAULT 'PRINCIPAL',
                    departure_id bigint NOT NULL REFERENCES trips_departure(id),
                    conducteur_id bigint NOT NULL REFERENCES gareci_admin_conducteur(id)
                )
                """
            )

        if not table_exists("gareci_admin_politiquereservation"):
            cursor.execute(
                """
                CREATE TABLE gareci_admin_politiquereservation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delai_max_avant_depart integer unsigned NOT NULL DEFAULT 90,
                    delai_min_avant_depart integer unsigned NOT NULL DEFAULT 2,
                    places_max_par_reservation integer unsigned NOT NULL DEFAULT 10,
                    reservations_max_par_client integer unsigned NOT NULL DEFAULT 5,
                    annulation_gratuite_heures integer unsigned NOT NULL DEFAULT 24,
                    penalite_annulation_pct integer unsigned NOT NULL DEFAULT 20,
                    delai_paiement_minutes integer unsigned NOT NULL DEFAULT 30,
                    active bool NOT NULL DEFAULT 1
                )
                """
            )


class Migration(migrations.Migration):
    dependencies = [
        ("gareci_admin", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(ensure_gareci_admin_schema, migrations.RunPython.noop)],
            state_operations=[
                migrations.RenameField(model_name="conducteur", old_name="contact", new_name="telephone"),
                migrations.RenameField(model_name="conducteur", old_name="permis", new_name="numero_permis"),
                migrations.RemoveField(model_name="conducteur", name="date_de_naissance"),
                migrations.RemoveField(model_name="conducteur", name="actif"),
                migrations.RemoveField(model_name="conducteur", name="bus"),
                migrations.AddField(model_name="conducteur", name="cin", field=models.CharField(default="CIN-TMP", max_length=50, unique=True), preserve_default=False),
                migrations.AddField(
                    model_name="conducteur",
                    name="type_permis",
                    field=models.CharField(blank=True, choices=[("D", "D"), ("DE", "DE")], max_length=3, null=True),
                ),
                migrations.AddField(model_name="conducteur", name="date_expiration_permis", field=models.DateField(blank=True, null=True)),
                migrations.AddField(model_name="conducteur", name="statut", field=models.CharField(choices=[("ACTIF", "Actif"), ("CONGE", "En congé"), ("SUSPENDU", "Suspendu")], default="ACTIF", max_length=10)),
                migrations.AddField(model_name="conducteur", name="photo", field=models.ImageField(blank=True, null=True, upload_to="conducteurs/")),
                migrations.CreateModel(
                    name="AffectationConducteur",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("role", models.CharField(choices=[("PRINCIPAL", "Principal"), ("REMPLACANT", "Remplaçant")], default="PRINCIPAL", max_length=12)),
                        ("conducteur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="affectations", to="gareci_admin.conducteur")),
                        ("departure", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="affectations_conducteurs", to="trips.departure")),
                    ],
                    options={"verbose_name": "Affectation Conducteur", "verbose_name_plural": "Affectations Conducteurs"},
                ),
                migrations.CreateModel(
                    name="PolitiqueReservation",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("delai_max_avant_depart", models.PositiveIntegerField(default=90, help_text="Nombre de jours maximum avant le départ pour réserver")),
                        ("delai_min_avant_depart", models.PositiveIntegerField(default=2, help_text="Nombre d'heures minimum avant le départ pour réserver")),
                        ("places_max_par_reservation", models.PositiveIntegerField(default=10)),
                        ("reservations_max_par_client", models.PositiveIntegerField(default=5)),
                        ("annulation_gratuite_heures", models.PositiveIntegerField(default=24)),
                        ("penalite_annulation_pct", models.PositiveIntegerField(default=20)),
                        ("delai_paiement_minutes", models.PositiveIntegerField(default=30)),
                        ("active", models.BooleanField(default=True)),
                    ],
                    options={"verbose_name": "Politique de réservation", "verbose_name_plural": "Politiques de réservation"},
                ),
            ],
        ),
    ]
