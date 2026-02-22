import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def ensure_reservations_schema(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "sqlite":
        return

    Ticket = apps.get_model("reservations", "Ticket")

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

        if table_exists("reservations_reservation"):
            add_col("reservations_reservation", "ticket_id bigint")
            add_col("reservations_reservation", "reference varchar(12)")
            add_col("reservations_reservation", "nombre_places smallint unsigned DEFAULT 1")
            add_col("reservations_reservation", "prix_total decimal DEFAULT 0")
            add_col("reservations_reservation", "expires_at datetime")
            add_col("reservations_reservation", "motif_rejet text")
            add_col("reservations_reservation", "validee_par_id bigint")
            add_col("reservations_reservation", "validee_at datetime")

            cursor.execute(
                """
                UPDATE reservations_reservation
                SET status = CASE status
                    WHEN 'P' THEN 'EN_ATTENTE_VALIDATION'
                    WHEN 'C' THEN 'CONFIRMEE'
                    WHEN 'X' THEN 'ANNULEE'
                    ELSE status
                END
                """
            )

        if not table_exists("reservations_paiement"):
            cursor.execute(
                """
                CREATE TABLE reservations_paiement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    montant decimal NOT NULL,
                    statut varchar(20) NOT NULL DEFAULT 'EN_ATTENTE',
                    reference_paiement varchar(20) NOT NULL UNIQUE,
                    created_at datetime NOT NULL,
                    updated_at datetime NOT NULL,
                    reservation_id bigint NOT NULL UNIQUE REFERENCES reservations_reservation(id)
                )
                """
            )

    # Populate missing ticket for legacy reservations
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT r.id, r.departure_id, r.user_id, r.nombre_places, r.prix_total, r.reference
            FROM reservations_reservation r
            WHERE r.ticket_id IS NULL
            """
        )
        missing_rows = cursor.fetchall()

    for reservation_id, departure_id, user_id, nombre_places, prix_total, reference in missing_rows:
        if not departure_id or not user_id:
            continue
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT bus_id FROM trips_departure WHERE id = %s LIMIT 1",
                [departure_id],
            )
            dep_row = cursor.fetchone()
        if not dep_row:
            continue
        bus_id = dep_row[0]
        ticket = Ticket.objects.create(
            bus_id=bus_id,
            user_id=user_id,
            num_seiges=nombre_places or 1,
            prix=prix_total or 0,
            code_qr_uuid=uuid.uuid4(),
        )
        values = [ticket.id]
        sql = "UPDATE reservations_reservation SET ticket_id = %s"
        if not reference:
            sql += ", reference = %s"
            values.append(f"LEGACY{reservation_id:06d}"[:12])
        sql += " WHERE id = %s"
        values.append(reservation_id)
        with conn.cursor() as cursor:
            cursor.execute(sql, values)

    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE reservations_reservation "
            "SET reference = 'LEGACY' || substr('000000' || id, -6, 6) "
            "WHERE reference IS NULL OR TRIM(reference) = ''"
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS reservations_reservation_reference_uniq "
            "ON reservations_reservation(reference)"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("trips", "0004_schema_alignment"),
        ("gareci_admin", "0002_schema_alignment"),
        ("reservations", "0003_reservation_seat_number_ticket"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(ensure_reservations_schema, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name="reservation",
                    name="ticket",
                    field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to="reservations.ticket"),
                    preserve_default=False,
                ),
                migrations.AlterField(
                    model_name="reservation",
                    name="status",
                    field=models.CharField(
                        choices=[
                            ("EN_ATTENTE_VALIDATION", "En attente de validation"),
                            ("VALIDEE", "Validée"),
                            ("CONFIRMEE", "Confirmée"),
                            ("REJETEE", "Rejetée"),
                            ("ANNULEE", "Annulée"),
                            ("EXPIREE", "Expirée"),
                        ],
                        default="EN_ATTENTE_VALIDATION",
                        max_length=25,
                    ),
                ),
                migrations.AddField(model_name="reservation", name="reference", field=models.CharField(blank=True, max_length=12, unique=True)),
                migrations.AddField(model_name="reservation", name="nombre_places", field=models.PositiveSmallIntegerField(default=1)),
                migrations.AddField(model_name="reservation", name="prix_total", field=models.DecimalField(decimal_places=2, default=0, max_digits=10), preserve_default=False),
                migrations.AddField(model_name="reservation", name="expires_at", field=models.DateTimeField(blank=True, null=True)),
                migrations.AddField(model_name="reservation", name="motif_rejet", field=models.TextField(blank=True)),
                migrations.AddField(model_name="reservation", name="validee_at", field=models.DateTimeField(blank=True, null=True)),
                migrations.AddField(
                    model_name="reservation",
                    name="validee_par",
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="validated_reservations", to=settings.AUTH_USER_MODEL),
                ),
                migrations.CreateModel(
                    name="Paiement",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("montant", models.DecimalField(decimal_places=2, max_digits=8)),
                        (
                            "statut",
                            models.CharField(
                                choices=[
                                    ("EN_ATTENTE", "En attente"),
                                    ("REUSSI", "Réussi"),
                                    ("ECHOUE", "Échoué"),
                                    ("ANNULE", "Annulé"),
                                ],
                                default="EN_ATTENTE",
                                max_length=20,
                            ),
                        ),
                        ("reference_paiement", models.CharField(editable=False, max_length=20, unique=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("reservation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="paiement", to="reservations.reservation")),
                    ],
                ),
            ],
        ),
    ]
