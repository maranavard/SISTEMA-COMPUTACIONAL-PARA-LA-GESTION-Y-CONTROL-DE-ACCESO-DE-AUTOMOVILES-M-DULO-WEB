"""Modelo de vehiculos compatible con distintos esquemas existentes.

Soporta tablas `public.vehiculos` o `public.vehicles`.
"""

from datetime import date
import re
import unicodedata

from psycopg2 import sql

from app.db import get_connection
from app.models.documento_vehiculo import DocumentoVehiculo
from app.utils.local_sync import LocalSyncService


class Vehiculo:
    @staticmethod
    def normalize_plate(placa: str) -> str:
        raw = (placa or "").strip().upper()
        # Acepta entradas con espacios/guiones y las normaliza a formato compacto.
        return re.sub(r"[^A-Z0-9]", "", raw)

    @classmethod
    def resolve_vehicle_type_name(cls, tipo_vehiculo_id: str | int | None) -> str:
        if tipo_vehiculo_id in (None, ""):
            return ""

        tipo_id = str(tipo_vehiculo_id).strip()
        if not tipo_id:
            return ""

        for item in cls.list_vehicle_types():
            if str(item.get("id")) == tipo_id:
                return str(item.get("nombre") or "").strip().lower()
        return ""

    @classmethod
    def validate_plate_format(cls, placa: str, tipo_vehiculo_id: str | int | None) -> tuple[bool, str]:
        plate = cls.normalize_plate(placa)
        tipo_nombre = cls.resolve_vehicle_type_name(tipo_vehiculo_id)

        if not plate:
            return False, "Debes ingresar una placa válida."

        if tipo_nombre == "automóvil":
            if not re.fullmatch(r"[A-Z]{3}[0-9]{3}", plate):
                return False, "Formato inválido para automóvil. Usa 3 letras y 3 números (ej: ABC123)."
            return True, ""

        if tipo_nombre == "motocicleta":
            if not re.fullmatch(r"[A-Z]{3}[0-9]{2}[A-Z]?", plate):
                return False, (
                    "Formato inválido para motocicleta. Usa 3 letras, 2 números y 1 letra opcional "
                    "(ej: ABC12D o ABC12)."
                )
            return True, ""

        return True, ""

    @staticmethod
    def list_vehicle_types() -> list[dict]:
        table_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('tipo_vehiculo', 'tipos_vehiculo', 'tipo_vehiculos')
            ORDER BY CASE table_name
                WHEN 'tipo_vehiculo' THEN 0
                WHEN 'tipos_vehiculo' THEN 1
                ELSE 2
            END
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(table_query)
                row = cur.fetchone()
                if not row:
                    return []

                table_name = row[0]
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    """,
                    (table_name,),
                )
                cols = {r[0] for r in cur.fetchall()}

                id_col = "id" if "id" in cols else ("id_tipo_vehiculo" if "id_tipo_vehiculo" in cols else None)
                if not id_col:
                    return []

                nombre_col = None
                for candidate in ("nombre", "tipo", "descripcion", "codigo"):
                    if candidate in cols:
                        nombre_col = candidate
                        break

                if not nombre_col:
                    return []

                query = f"""
                    SELECT {id_col} AS id, {nombre_col} AS nombre
                    FROM public.{table_name}
                    ORDER BY {nombre_col}
                """
                cur.execute(query)
                rows = cur.fetchall()

        def _normalize_text(value: str) -> str:
            text = (value or "").strip().lower()
            text = unicodedata.normalize("NFKD", text)
            text = "".join(ch for ch in text if not unicodedata.combining(ch))
            return text

        canonical_labels = {
            "automovil": "automóvil",
            "motocicleta": "motocicleta",
            "bus": "bus",
            "camion": "camión",
        }

        found: dict[str, dict] = {}
        for row in rows:
            item_id, raw_name = row[0], str(row[1] or "")
            name = _normalize_text(raw_name)

            matched_key = None
            if any(token in name for token in ("bus", "autobus", "buseta", "microbus")):
                matched_key = "bus"
            elif any(token in name for token in ("motocicleta", "moto")):
                matched_key = "motocicleta"
            elif any(token in name for token in ("camion",)):
                matched_key = "camion"
            elif any(token in name for token in ("automovil", "auto", "carro", "sedan", "particular")):
                matched_key = "automovil"

            if matched_key and matched_key not in found:
                found[matched_key] = {"id": item_id, "nombre": canonical_labels[matched_key]}

        ordered_keys = ["automovil", "motocicleta", "bus", "camion"]
        default_ids = {
            "automovil": 1,
            "motocicleta": 2,
            "bus": 3,
            "camion": 4,
        }

        result = []
        for key in ordered_keys:
            if key in found:
                result.append(found[key])
            else:
                result.append({"id": default_ids[key], "nombre": canonical_labels[key]})

        return result

    @staticmethod
    def _get_table_name() -> str:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('vehiculos', 'vehicles')
            ORDER BY CASE table_name WHEN 'vehiculos' THEN 0 ELSE 1 END
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
        return row[0] if row else "vehiculos"

    @staticmethod
    def _get_columns(table_name: str) -> set[str]:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table_name,))
                return {row[0] for row in cur.fetchall()}

    @classmethod
    def list_items(cls) -> list[dict]:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        tipo_nombre_expr = (
            "(SELECT tv.nombre FROM public.tipo_vehiculo tv WHERE tv.id = v.tipo_vehiculo_id LIMIT 1) AS tipo_vehiculo_nombre"
            if "tipo_vehiculo_id" in cols
            else "NULL::text AS tipo_vehiculo_nombre"
        )

        select_map = {
            "id": "v.id",
            "placa": "v.placa" if "placa" in cols else "NULL::text AS placa",
            "tipo_vehiculo_id": "v.tipo_vehiculo_id" if "tipo_vehiculo_id" in cols else "NULL::int AS tipo_vehiculo_id",
            "tipo_vehiculo_nombre": tipo_nombre_expr,
            "marca": "v.marca" if "marca" in cols else "NULL::text AS marca",
            "modelo": "v.modelo" if "modelo" in cols else "NULL::text AS modelo",
            "color": "v.color" if "color" in cols else "NULL::text AS color",
            "fecha_registro": "v.fecha_registro" if "fecha_registro" in cols else "NULL::timestamp AS fecha_registro",
            "estado": "v.estado" if "estado" in cols else "NULL::text AS estado",
            "conductor_id": "v.conductor_id" if "conductor_id" in cols else "NULL::int AS conductor_id",
            "user_id": "v.user_id" if "user_id" in cols else "NULL::int AS user_id",
        }

        query = f"""
            SELECT
                {select_map['id']},
                {select_map['placa']},
                {select_map['tipo_vehiculo_id']},
                {select_map['tipo_vehiculo_nombre']},
                {select_map['marca']},
                {select_map['modelo']},
                {select_map['color']},
                {select_map['fecha_registro']},
                {select_map['estado']},
                {select_map['conductor_id']},
                {select_map['user_id']}
            FROM public.{table_name} v
            ORDER BY v.id DESC
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "placa": row[1],
                "tipo_vehiculo_id": row[2],
                "tipo_vehiculo_nombre": row[3],
                "marca": row[4],
                "modelo": row[5],
                "color": row[6],
                "fecha_registro": row[7],
                "estado": row[8],
                "conductor_id": row[9],
                "user_id": row[10],
            }
            for row in rows
        ]

    @classmethod
    def get_by_placa(cls, placa: str) -> dict | None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)
        if "placa" not in cols:
            return None

        tipo_nombre_expr = (
            "(SELECT tv.nombre FROM public.tipo_vehiculo tv WHERE tv.id = v.tipo_vehiculo_id LIMIT 1) AS tipo_vehiculo_nombre"
            if "tipo_vehiculo_id" in cols
            else "NULL::text AS tipo_vehiculo_nombre"
        )

        query = f"""
            SELECT
                v.id,
                v.placa,
                {tipo_nombre_expr},
                {"v.marca" if "marca" in cols else "NULL::text"},
                {"v.modelo" if "modelo" in cols else "NULL::text"},
                {"v.color" if "color" in cols else "NULL::text"},
                {"v.fecha_registro" if "fecha_registro" in cols else "NULL::timestamp"},
                {"v.estado" if "estado" in cols else "NULL::text"}
            FROM public.{table_name} v
            WHERE upper(v.placa) = upper(%s)
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (placa,))
                row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "placa": row[1],
            "tipo_vehiculo_nombre": row[2],
            "marca": row[3],
            "modelo": row[4],
            "color": row[5],
            "fecha_registro": row[6],
            "estado": row[7],
        }

    @classmethod
    def get_by_id(cls, item_id: int) -> dict | None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        tipo_nombre_expr = (
            "(SELECT tv.nombre FROM public.tipo_vehiculo tv WHERE tv.id = v.tipo_vehiculo_id LIMIT 1) AS tipo_vehiculo_nombre"
            if "tipo_vehiculo_id" in cols
            else "NULL::text AS tipo_vehiculo_nombre"
        )

        query = f"""
            SELECT
                v.id,
                {"v.placa" if "placa" in cols else "NULL::text"},
                {tipo_nombre_expr},
                {"v.tipo_vehiculo_id" if "tipo_vehiculo_id" in cols else "NULL::int"},
                {"v.marca" if "marca" in cols else "NULL::text"},
                {"v.modelo" if "modelo" in cols else "NULL::text"},
                {"v.color" if "color" in cols else "NULL::text"},
                {"v.fecha_registro" if "fecha_registro" in cols else "NULL::timestamp"},
                {"v.estado" if "estado" in cols else "NULL::text"},
                {"v.conductor_id" if "conductor_id" in cols else "NULL::int"},
                {"v.user_id" if "user_id" in cols else "NULL::int"}
            FROM public.{table_name} v
            WHERE v.id = %s
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (item_id,))
                row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "placa": row[1],
            "tipo_vehiculo_nombre": row[2],
            "tipo_vehiculo_id": row[3],
            "marca": row[4],
            "modelo": row[5],
            "color": row[6],
            "fecha_registro": row[7],
            "estado": row[8],
            "conductor_id": row[9],
            "user_id": row[10],
        }

    @classmethod
    def create_item(cls, data: dict) -> int | None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        if "placa" in cols and not data.get("placa"):
            raise ValueError("La placa es obligatoria")

        allowed_fields = [
            "placa",
            "tipo_vehiculo_id",
            "marca",
            "modelo",
            "color",
            "fecha_registro",
            "estado",
            "conductor_id",
            "user_id",
        ]

        insert_cols = []
        insert_vals = []
        for field in allowed_fields:
            if field not in cols:
                continue

            value = data.get(field)
            if value in (None, ""):
                continue

            insert_cols.append(field)
            insert_vals.append(value)

        if not insert_cols:
            return

        query = sql.SQL("INSERT INTO public.{table} ({fields}) VALUES ({values}) RETURNING id").format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(", ").join(sql.Identifier(column_name) for column_name in insert_cols),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in insert_cols),
        )

        inserted_id = None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, insert_vals)
                row = cur.fetchone()
                if row:
                    inserted_id = row[0]
            conn.commit()

        try:
            LocalSyncService.sync_event(entidad="vehiculos", operacion="upsert", payload=data)
        except Exception:
            pass

        return inserted_id

    @classmethod
    def update_item(cls, item_id: int, data: dict) -> None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        allowed_fields = [
            "placa",
            "tipo_vehiculo_id",
            "marca",
            "modelo",
            "color",
            "fecha_registro",
            "estado",
            "conductor_id",
            "user_id",
        ]

        assignments = []
        values = []
        for field in allowed_fields:
            if field in cols and field in data:
                assignments.append(sql.SQL("{} = {}").format(sql.Identifier(field), sql.Placeholder()))
                values.append(data[field] if data[field] != "" else None)

        if not assignments:
            return

        values.append(item_id)
        query = sql.SQL("UPDATE public.{table} SET {assignments} WHERE id = %s").format(
            table=sql.Identifier(table_name),
            assignments=sql.SQL(", ").join(assignments),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

        try:
            current = cls.get_by_id(item_id)
            payload = dict(data)
            if current and current.get("placa") and not payload.get("placa"):
                payload["placa"] = current.get("placa")
            LocalSyncService.sync_event(entidad="vehiculos", operacion="upsert", payload=payload)
        except Exception:
            pass

    @classmethod
    def delete_item(cls, item_id: int) -> None:
        table_name = cls._get_table_name()
        query = sql.SQL("DELETE FROM public.{table} WHERE id = %s").format(table=sql.Identifier(table_name))

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (item_id,))
            conn.commit()

    @classmethod
    def get_document_status_by_placa(cls, placa: str, warning_days: int = 30) -> dict:
        plate = (placa or "").strip().upper()
        if not plate:
            return {
                "ok": False,
                "level": "error",
                "message": "Debes indicar una placa para validar documentación.",
                "block_automatic_assignment": True,
            }

        veh_table = cls._get_table_name()
        veh_cols = cls._get_columns(veh_table)
        if "placa" not in veh_cols:
            return {
                "ok": False,
                "level": "error",
                "message": "La tabla de vehículos no contiene columna placa para validar documentación.",
                "block_automatic_assignment": True,
            }

        conductor_fk_col = "conductor_id" if "conductor_id" in veh_cols else None
        user_fk_col = "user_id" if "user_id" in veh_cols else None

        query_vehicle = f"""
            SELECT
                v.id,
                v.placa,
                {f'v.{conductor_fk_col}' if conductor_fk_col else 'NULL::int'} AS conductor_id,
                {f'v.{user_fk_col}' if user_fk_col else 'NULL::int'} AS user_id
            FROM public.{veh_table} v
            WHERE upper(v.placa) = upper(%s)
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query_vehicle, (plate,))
                vehicle_row = cur.fetchone()

        if not vehicle_row:
            return {
                "ok": False,
                "level": "error",
                "message": f"La placa {plate} no está registrada en el sistema.",
                "block_automatic_assignment": True,
            }

        vehicle_doc_status = DocumentoVehiculo.get_status_summary(
            vehiculo_id=int(vehicle_row[0]),
            warning_days=warning_days,
        )
        if not vehicle_doc_status.get("ok"):
            return {
                "ok": False,
                "level": "error",
                "message": f"{vehicle_doc_status.get('message') or 'Documentación vehicular inválida.'}",
                "block_automatic_assignment": True,
            }

        vehicle_warning_text = ""
        if (vehicle_doc_status.get("level") or "").strip().lower() == "warning":
            vehicle_warning_text = str(vehicle_doc_status.get("message") or "").strip()

        conductor_id = vehicle_row[2]
        if conductor_id is None:
            return {
                "ok": False,
                "level": "error",
                "message": f"El vehículo {plate} no tiene conductor asociado. Validación documental manual requerida.",
                "block_automatic_assignment": True,
            }

        # Compatibilidad de tabla de conductores.
        query_table = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('conductores', 'conductors')
            ORDER BY CASE table_name WHEN 'conductores' THEN 0 ELSE 1 END
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query_table)
                row_table = cur.fetchone()
                conductor_table = row_table[0] if row_table else "conductores"

                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    """,
                    (conductor_table,),
                )
                conductor_cols = {r[0] for r in cur.fetchall()}

        fecha_col = "fecha_vencimiento_pase" if "fecha_vencimiento_pase" in conductor_cols else None
        numero_pase_col = "numero_pase" if "numero_pase" in conductor_cols else None
        estado_col = "estado" if "estado" in conductor_cols else None
        nombre_col = "nombre" if "nombre" in conductor_cols else None
        apellido_col = "apellido" if "apellido" in conductor_cols else None

        if fecha_col is None:
            return {
                "ok": False,
                "level": "error",
                "message": "No existe fecha de vencimiento de pase en la tabla de conductores.",
                "block_automatic_assignment": True,
            }

        query_conductor = f"""
            SELECT
                c.id,
                {f'c.{nombre_col}' if nombre_col else 'NULL::text'} AS nombre,
                {f'c.{apellido_col}' if apellido_col else 'NULL::text'} AS apellido,
                {f'c.{numero_pase_col}' if numero_pase_col else 'NULL::text'} AS numero_pase,
                c.{fecha_col} AS fecha_vencimiento_pase,
                {f'c.{estado_col}' if estado_col else "'activo'::text"} AS estado
            FROM public.{conductor_table} c
            WHERE c.id = %s
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query_conductor, (conductor_id,))
                conductor_row = cur.fetchone()

        if not conductor_row:
            return {
                "ok": False,
                "level": "error",
                "message": f"No se encontró conductor asociado al vehículo {plate}.",
                "block_automatic_assignment": True,
            }

        numero_pase = conductor_row[3]
        fecha_vence = conductor_row[4]
        estado_conductor = (conductor_row[5] or "").strip().lower()

        if not numero_pase:
            return {
                "ok": False,
                "level": "error",
                "message": f"El conductor del vehículo {plate} no tiene número de pase registrado.",
                "block_automatic_assignment": True,
            }

        if fecha_vence is None:
            return {
                "ok": False,
                "level": "error",
                "message": f"El conductor del vehículo {plate} no tiene fecha de vencimiento del pase.",
                "block_automatic_assignment": True,
            }

        if hasattr(fecha_vence, "date"):
            fecha_vence = fecha_vence.date()
        if not isinstance(fecha_vence, date):
            return {
                "ok": False,
                "level": "error",
                "message": f"No se pudo interpretar la fecha de vencimiento del pase para {plate}.",
                "block_automatic_assignment": True,
            }

        days_to_expire = (fecha_vence - date.today()).days
        if estado_conductor == "inactivo":
            return {
                "ok": False,
                "level": "error",
                "message": f"Conductor inactivo para la placa {plate}. Se requiere validación manual.",
                "block_automatic_assignment": True,
            }

        if days_to_expire < 0:
            return {
                "ok": False,
                "level": "error",
                "message": f"Documento vencido para {plate} ({abs(days_to_expire)} días). Acceso sujeto a validación manual.",
                "block_automatic_assignment": True,
            }

        if days_to_expire <= warning_days:
            warning_parts = [f"Alerta documental: pase de {plate} vence en {days_to_expire} días."]
            if vehicle_warning_text:
                warning_parts.append(vehicle_warning_text)
            return {
                "ok": True,
                "level": "warning",
                "message": " ".join(warning_parts),
                "block_automatic_assignment": False,
            }

        if vehicle_warning_text:
            return {
                "ok": True,
                "level": "warning",
                "message": vehicle_warning_text,
                "block_automatic_assignment": False,
            }

        return {
            "ok": True,
            "level": "success",
            "message": f"Documentación vigente para {plate} (conductor y vehículo).",
            "block_automatic_assignment": False,
        }
