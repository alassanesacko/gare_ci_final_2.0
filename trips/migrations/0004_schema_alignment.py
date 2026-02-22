from django.db import migrations, models
import django.db.models.deletion


def ensure_trips_schema(apps, schema_editor):
    conn = schema_editor.connection
    vendor = conn.vendor
    if vendor != "sqlite":
        # This project currently uses SQLite in settings. Keep migration safe on other DBs.
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

        if not table_exists("trips_ville"):
            cursor.execute(
                """
                CREATE TABLE trips_ville (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom varchar(100) NOT NULL,
                    code varchar(10) NOT NULL UNIQUE
                )
                """
            )

        if not table_exists("trips_arret"):
            cursor.execute(
                """
                CREATE TABLE trips_arret (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom varchar(100) NOT NULL,
                    adresse varchar(200) NOT NULL,
                    ville_id bigint NOT NULL REFERENCES trips_ville(id)
                )
                """
            )

        if not table_exists("trips_segment"):
            cursor.execute(
                """
                CREATE TABLE trips_segment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    distance_km decimal NOT NULL,
                    duree_minutes integer unsigned NOT NULL,
                    arret_arrivee_id bigint NOT NULL REFERENCES trips_arret(id),
                    arret_depart_id bigint NOT NULL REFERENCES trips_arret(id)
                )
                """
            )

        if not table_exists("trips_etapetrajet"):
            cursor.execute(
                """
                CREATE TABLE trips_etapetrajet (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ordre integer unsigned NOT NULL,
                    segment_id bigint NOT NULL REFERENCES trips_segment(id),
                    trip_id bigint NOT NULL REFERENCES trips_trip(id)
                )
                """
            )
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS trips_etapetrajet_trip_id_ordre_uniq
                ON trips_etapetrajet(trip_id, ordre)
                """
            )

        cursor.execute("SELECT id FROM trips_ville WHERE code='LEGACY' LIMIT 1")
        row = cursor.fetchone()
        if row:
            legacy_ville_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO trips_ville (nom, code) VALUES (%s, %s)",
                ["Ville legacy", "LEGACY"],
            )
            legacy_ville_id = cursor.lastrowid

        cursor.execute("SELECT id FROM trips_arret WHERE nom='Arret legacy' LIMIT 1")
        row = cursor.fetchone()
        if row:
            legacy_arret_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO trips_arret (nom, adresse, ville_id) VALUES (%s, %s, %s)",
                ["Arret legacy", "Adresse legacy", legacy_ville_id],
            )
            legacy_arret_id = cursor.lastrowid

        if table_exists("trips_category"):
            add_col("trips_category", "nom varchar(100)")
            add_col("trips_category", "niveau varchar(20) DEFAULT 'ECONOMIQUE'")
            add_col("trips_category", "prix_multiplicateur decimal DEFAULT 1.00")
            add_col("trips_category", "a_wifi bool DEFAULT 0")
            add_col("trips_category", "a_climatisation bool DEFAULT 0")
            add_col("trips_category", "a_prise_usb bool DEFAULT 0")
            add_col("trips_category", "a_wc bool DEFAULT 0")
            add_col("trips_category", "a_repas bool DEFAULT 0")
            add_col("trips_category", "a_couchette bool DEFAULT 0")
            cursor.execute(
                "UPDATE trips_category SET nom = COALESCE(nom, name)"
            )

        if table_exists("trips_bus"):
            add_col("trips_bus", "immatriculation varchar(50)")
            add_col("trips_bus", "modele varchar(150)")
            add_col("trips_bus", "capacite integer")
            add_col("trips_bus", "categorie_id bigint REFERENCES trips_category(id)")
            add_col("trips_bus", "annee_fabrication integer")
            add_col("trips_bus", "en_service bool DEFAULT 1")
            add_col("trips_bus", "photo varchar(100)")
            add_col("trips_bus", "derniere_revision date")
            cursor.execute(
                "UPDATE trips_bus SET capacite = COALESCE(capacite, capacity)"
            )
            cursor.execute(
                "UPDATE trips_bus SET immatriculation = COALESCE(immatriculation, name)"
            )
            cursor.execute(
                "UPDATE trips_bus SET immatriculation = 'BUS-' || id "
                "WHERE immatriculation IS NULL OR TRIM(immatriculation) = ''"
            )
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS trips_bus_immatriculation_uniq "
                "ON trips_bus(immatriculation)"
            )

        if table_exists("trips_trip"):
            add_col("trips_trip", "nom varchar(100)")
            add_col("trips_trip", "ville_depart_id bigint")
            add_col("trips_trip", "ville_arrivee_id bigint")
            add_col("trips_trip", "arret_depart_id bigint")
            add_col("trips_trip", "arret_arrivee_id bigint")
            add_col("trips_trip", "actif bool DEFAULT 1")
            cursor.execute(
                "UPDATE trips_trip SET nom = COALESCE(nom, origin || ' - ' || destination)"
            )
            cursor.execute(
                "UPDATE trips_trip SET ville_depart_id = COALESCE(ville_depart_id, %s)",
                [legacy_ville_id],
            )
            cursor.execute(
                "UPDATE trips_trip SET ville_arrivee_id = COALESCE(ville_arrivee_id, %s)",
                [legacy_ville_id],
            )
            cursor.execute(
                "UPDATE trips_trip SET arret_depart_id = COALESCE(arret_depart_id, %s)",
                [legacy_arret_id],
            )
            cursor.execute(
                "UPDATE trips_trip SET arret_arrivee_id = COALESCE(arret_arrivee_id, %s)",
                [legacy_arret_id],
            )

        if table_exists("trips_departure"):
            add_col("trips_departure", "date_depart datetime")
            add_col("trips_departure", "date_arrivee_estimee datetime")
            add_col("trips_departure", "places_disponibles integer DEFAULT 0")
            add_col("trips_departure", "actif bool DEFAULT 1")
            cursor.execute(
                """
                UPDATE trips_departure
                SET date_depart = COALESCE(date_depart, datetime(date || ' ' || time))
                """
            )
            cursor.execute(
                """
                UPDATE trips_departure
                SET date_arrivee_estimee = COALESCE(
                    date_arrivee_estimee,
                    datetime(date || ' ' || time, '+4 hours')
                )
                """
            )
            cursor.execute(
                """
                UPDATE trips_departure
                SET places_disponibles = COALESCE(
                    places_disponibles,
                    (SELECT COALESCE(capacite, capacity, 0)
                     FROM trips_bus b
                     WHERE b.id = trips_departure.bus_id),
                    0
                )
                """
            )
            cursor.execute(
                "UPDATE trips_departure SET actif = COALESCE(actif, is_active, 1)"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("trips", "0003_alter_departure_options"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(ensure_trips_schema, migrations.RunPython.noop)],
            state_operations=[
                migrations.CreateModel(
                    name="Ville",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("nom", models.CharField(max_length=100)),
                        ("code", models.CharField(max_length=10, unique=True)),
                    ],
                ),
                migrations.CreateModel(
                    name="Arret",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("nom", models.CharField(max_length=100)),
                        ("adresse", models.CharField(max_length=200)),
                        ("ville", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="trips.ville")),
                    ],
                ),
                migrations.CreateModel(
                    name="Segment",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("distance_km", models.DecimalField(decimal_places=2, max_digits=10)),
                        ("duree_minutes", models.PositiveIntegerField()),
                        ("arret_arrivee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="segments_arrivee", to="trips.arret")),
                        ("arret_depart", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="segments_depart", to="trips.arret")),
                    ],
                ),
                migrations.CreateModel(
                    name="EtapeTrajet",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("ordre", models.PositiveIntegerField()),
                        ("segment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="trips.segment")),
                        ("trip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="trips.trip")),
                    ],
                    options={"ordering": ["ordre"], "unique_together": {("trip", "ordre")}},
                ),
                migrations.RenameField(model_name="category", old_name="name", new_name="nom"),
                migrations.AddField(
                    model_name="category",
                    name="niveau",
                    field=models.CharField(
                        choices=[("ECONOMIQUE", "Economique"), ("CONFORT", "Confort"), ("VIP", "VIP"), ("NUIT", "Nuit")],
                        default="ECONOMIQUE",
                        max_length=20,
                    ),
                ),
                migrations.AddField(model_name="category", name="prix_multiplicateur", field=models.DecimalField(decimal_places=2, default=1.0, max_digits=5)),
                migrations.AddField(model_name="category", name="a_wifi", field=models.BooleanField(default=False)),
                migrations.AddField(model_name="category", name="a_climatisation", field=models.BooleanField(default=False)),
                migrations.AddField(model_name="category", name="a_prise_usb", field=models.BooleanField(default=False)),
                migrations.AddField(model_name="category", name="a_wc", field=models.BooleanField(default=False)),
                migrations.AddField(model_name="category", name="a_repas", field=models.BooleanField(default=False)),
                migrations.AddField(model_name="category", name="a_couchette", field=models.BooleanField(default=False)),
                migrations.RenameField(model_name="bus", old_name="name", new_name="immatriculation"),
                migrations.RenameField(model_name="bus", old_name="capacity", new_name="capacite"),
                migrations.AddField(model_name="bus", name="modele", field=models.CharField(blank=True, max_length=150)),
                migrations.AddField(
                    model_name="bus",
                    name="categorie",
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="buses", to="trips.category"),
                ),
                migrations.AddField(model_name="bus", name="annee_fabrication", field=models.PositiveIntegerField(blank=True, null=True)),
                migrations.AddField(model_name="bus", name="en_service", field=models.BooleanField(default=True)),
                migrations.AddField(model_name="bus", name="photo", field=models.ImageField(blank=True, null=True, upload_to="buses/")),
                migrations.AddField(model_name="bus", name="derniere_revision", field=models.DateField(blank=True, null=True)),
                migrations.AlterField(model_name="bus", name="immatriculation", field=models.CharField(max_length=50, unique=True)),
                migrations.RenameField(model_name="trip", old_name="origin", new_name="nom"),
                migrations.RemoveField(model_name="trip", name="description"),
                migrations.RemoveField(model_name="trip", name="destination"),
                migrations.RemoveField(model_name="trip", name="category"),
                migrations.AddField(model_name="trip", name="ville_depart", field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name="trips_depart", to="trips.ville"), preserve_default=False),
                migrations.AddField(model_name="trip", name="ville_arrivee", field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name="trips_arrivee", to="trips.ville"), preserve_default=False),
                migrations.AddField(model_name="trip", name="arret_depart", field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name="trips_depart", to="trips.arret"), preserve_default=False),
                migrations.AddField(model_name="trip", name="arret_arrivee", field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name="trips_arrivee", to="trips.arret"), preserve_default=False),
                migrations.AddField(model_name="trip", name="actif", field=models.BooleanField(default=True)),
                migrations.RenameField(model_name="departure", old_name="date", new_name="date_depart"),
                migrations.RenameField(model_name="departure", old_name="is_active", new_name="actif"),
                migrations.RemoveField(model_name="departure", name="time"),
                migrations.AddField(model_name="departure", name="date_arrivee_estimee", field=models.DateTimeField(default="2000-01-01T00:00:00"), preserve_default=False),
                migrations.AddField(model_name="departure", name="places_disponibles", field=models.PositiveIntegerField(default=0)),
                migrations.AlterField(model_name="departure", name="date_depart", field=models.DateTimeField()),
                migrations.AlterField(model_name="departure", name="places_disponibles", field=models.PositiveIntegerField()),
                migrations.AlterModelOptions(name="departure", options={"ordering": ["date_depart"]}),
            ],
        ),
    ]
