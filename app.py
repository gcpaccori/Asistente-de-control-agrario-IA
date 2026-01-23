from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import json
import os
import sqlite3
from flask import Flask, g, jsonify, redirect, render_template, request, url_for
from llama_cpp import Llama

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DB_PATH = INSTANCE_DIR / "app.db"

app = Flask(__name__, instance_path=str(INSTANCE_DIR))
app.config["DATABASE"] = str(DB_PATH)

def load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

LOCAL_MODEL_PATH = os.getenv(
    "LOCAL_MODEL_PATH", str(BASE_DIR / "models/qwen2.5-3b-instruct-q4_k_m.gguf")
)
N_CTX = int(os.getenv("N_CTX", "2048"))
N_THREADS = int(os.getenv("N_THREADS", "1"))
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/Lima")
DAILY_CHECKIN_HOUR = int(os.getenv("DAILY_CHECKIN_HOUR", "8"))

PROMPTS = {
    "formulario": (
        "Eres un asistente agrónomo por WhatsApp. Pregunta natural y breve. "
        "Extrae datos para completar el formulario, una bitácora diaria, y el avance de tareas. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log,bitacora,actualizar_tarea}, "
        "estado{formulario_completo,confianza}."
    ),
    "consulta": (
        "Responde usando SOLO la información del contexto. "
        "Si falta información, pide una sola aclaración. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log}, "
        "estado{formulario_completo,confianza}."
    ),
    "intervencion": (
        "Analiza persistencia o riesgo con el historial. "
        "Si amerita, genera alerta. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log}, "
        "estado{formulario_completo,confianza}."
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db() -> None:
    INSTANCE_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(app.config["DATABASE"])
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS producers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name TEXT,
            zone TEXT,
            preferred_language TEXT NOT NULL,
            main_crops TEXT,
            allowed INTEGER NOT NULL,
            status TEXT NOT NULL,
            timezone TEXT NOT NULL,
            last_checkin_date TEXT,
            assigned_role TEXT,
            enable_formulario INTEGER NOT NULL,
            enable_consulta INTEGER NOT NULL,
            enable_intervencion INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            cultivo TEXT,
            sintoma TEXT,
            inicio_problema TEXT,
            foto_recibida INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            level TEXT NOT NULL,
            reason TEXT NOT NULL,
            action TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sent_at TEXT,
            FOREIGN KEY (producer_id) REFERENCES producers (id)
        );

        CREATE TABLE IF NOT EXISTS log_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS agent_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT UNIQUE NOT NULL,
            enabled INTEGER NOT NULL,
            description TEXT NOT NULL,
            prompt TEXT NOT NULL,
            max_tokens INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id)
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            targets_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS producer_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id),
            FOREIGN KEY (plan_id) REFERENCES plans (id)
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            plan_id INTEGER,
            log_type_id INTEGER,
            log_date TEXT NOT NULL,
            notes TEXT NOT NULL,
            metrics_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id),
            FOREIGN KEY (plan_id) REFERENCES plans (id),
            FOREIGN KEY (log_type_id) REFERENCES log_types (id)
        );

        CREATE TABLE IF NOT EXISTS plan_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_type TEXT NOT NULL,
            tasks_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS producer_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            template_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            order_sequence INTEGER NOT NULL,
            status TEXT NOT NULL,
            estimated_date TEXT,
            completion_date TEXT,
            progress_pct INTEGER,
            blocker_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id),
            FOREIGN KEY (template_id) REFERENCES plan_templates (id)
        );
        """
    )
    db.commit()
    db.close()


def migrate_db() -> None:
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    columns = {
        row["name"] for row in db.execute("PRAGMA table_info(producers)").fetchall()
    }
    if "name" not in columns:
        db.execute("ALTER TABLE producers ADD COLUMN name TEXT")
    if "allowed" not in columns:
        db.execute("ALTER TABLE producers ADD COLUMN allowed INTEGER NOT NULL DEFAULT 0")
    if "status" not in columns:
        db.execute(
            "ALTER TABLE producers ADD COLUMN status TEXT NOT NULL DEFAULT 'activo'"
        )
    if "timezone" not in columns:
        db.execute(
            "ALTER TABLE producers ADD COLUMN timezone TEXT NOT NULL DEFAULT 'America/Lima'"
        )
    if "last_checkin_date" not in columns:
        db.execute("ALTER TABLE producers ADD COLUMN last_checkin_date TEXT")
    if "assigned_role" not in columns:
        db.execute("ALTER TABLE producers ADD COLUMN assigned_role TEXT")
    if "enable_formulario" not in columns:
        db.execute(
            "ALTER TABLE producers ADD COLUMN enable_formulario INTEGER NOT NULL DEFAULT 1"
        )
    if "enable_consulta" not in columns:
        db.execute(
            "ALTER TABLE producers ADD COLUMN enable_consulta INTEGER NOT NULL DEFAULT 1"
        )
    if "enable_intervencion" not in columns:
        db.execute(
            "ALTER TABLE producers ADD COLUMN enable_intervencion INTEGER NOT NULL DEFAULT 1"
        )

    alert_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(alerts)").fetchall()
    }
    if "message" not in alert_columns:
        db.execute("ALTER TABLE alerts ADD COLUMN message TEXT NOT NULL DEFAULT ''")
    if "sent_at" not in alert_columns:
        db.execute("ALTER TABLE alerts ADD COLUMN sent_at TEXT")

    message_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(messages)").fetchall()
    }
    if "status" not in message_columns:
        db.execute(
            "ALTER TABLE messages ADD COLUMN status TEXT NOT NULL DEFAULT 'entregado'"
        )
    daily_log_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(daily_logs)").fetchall()
    }
    if "log_type_id" not in daily_log_columns:
        db.execute("ALTER TABLE daily_logs ADD COLUMN log_type_id INTEGER")

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS log_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            targets_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS producer_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id),
            FOREIGN KEY (plan_id) REFERENCES plans (id)
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            plan_id INTEGER,
            log_type_id INTEGER,
            log_date TEXT NOT NULL,
            notes TEXT NOT NULL,
            metrics_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id),
            FOREIGN KEY (plan_id) REFERENCES plans (id),
            FOREIGN KEY (log_type_id) REFERENCES log_types (id)
        );

        CREATE TABLE IF NOT EXISTS plan_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_type TEXT NOT NULL,
            tasks_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS producer_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer_id INTEGER NOT NULL,
            template_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            order_sequence INTEGER NOT NULL,
            status TEXT NOT NULL,
            estimated_date TEXT,
            completion_date TEXT,
            progress_pct INTEGER,
            blocker_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id),
            FOREIGN KEY (template_id) REFERENCES plan_templates (id)
        );
        """
    )

    db.commit()
    db.close()


def ensure_agent_defaults() -> None:
    db = get_db()
    existing = {
        row["role"] for row in db.execute("SELECT role FROM agent_configs").fetchall()
    }
    for role, prompt in PROMPTS.items():
        if role not in existing:
            description = f"Agente {role} (configuración inicial)"
            db.execute(
                """
                INSERT INTO agent_configs (role, enabled, description, prompt, max_tokens)
                VALUES (?, ?, ?, ?, ?)
                """,
                (role, 1, description, prompt, 300),
            )
    db.commit()


def get_or_create_producer(phone: str) -> dict[str, Any]:
    db = get_db()
    row = db.execute("SELECT * FROM producers WHERE phone = ?", (phone,)).fetchone()
    if row:
        return dict(row)
    now = utc_now()
    db.execute(
        """
        INSERT INTO producers (
            phone, name, zone, preferred_language, main_crops, allowed, status,
            timezone, last_checkin_date, assigned_role, enable_formulario,
            enable_consulta, enable_intervencion, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            phone,
            None,
            None,
            "es",
            json.dumps([]),
            0,
            "activo",
            DEFAULT_TIMEZONE,
            None,
            None,
            1,
            1,
            1,
            now,
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM producers WHERE phone = ?", (phone,)).fetchone()
    return dict(row)


def get_or_create_form(producer_id: int) -> dict[str, Any]:
    db = get_db()
    row = db.execute(
        """
        SELECT * FROM forms
        WHERE producer_id = ? AND status = 'abierto'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (producer_id,),
    ).fetchone()
    if row:
        return dict(row)
    now = utc_now()
    db.execute(
        """
        INSERT INTO forms (producer_id, status, cultivo, sintoma, inicio_problema, foto_recibida, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (producer_id, "abierto", None, None, None, 0, now, now),
    )
    db.commit()
    row = db.execute(
        """
        SELECT * FROM forms
        WHERE producer_id = ? AND status = 'abierto'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (producer_id,),
    ).fetchone()
    return dict(row)


def get_active_task(producer_id: int) -> dict[str, Any] | None:
    db = get_db()
    row = db.execute(
        """
        SELECT *
        FROM producer_tasks
        WHERE producer_id = ?
          AND status IN ('PENDIENTE', 'EN_PROGRESO', 'BLOQUEADO')
        ORDER BY order_sequence ASC
        LIMIT 1
        """,
        (producer_id,),
    ).fetchone()
    if not row:
        return None
    return dict(row)


def build_tasks_from_template(
    template: dict[str, Any], start_date: date
) -> list[dict[str, Any]]:
    tasks = json.loads(template.get("tasks_json") or "[]")
    built: list[dict[str, Any]] = []
    last_date = start_date
    for raw in tasks:
        order = raw.get("order")
        name = raw.get("task")
        if order is None or not name:
            continue
        if "days_from_start" in raw:
            estimated = start_date + timedelta(days=int(raw["days_from_start"]))
        elif "days_after_previous" in raw:
            estimated = last_date + timedelta(days=int(raw["days_after_previous"]))
        else:
            estimated = last_date
        last_date = estimated
        built.append(
            {
                "order_sequence": int(order),
                "task_name": str(name),
                "estimated_date": estimated.isoformat(),
            }
        )
    return built


def assign_plan_to_producer(
    producer_id: int, template_id: int, start_date_str: str
) -> int:
    db = get_db()
    template = db.execute(
        "SELECT * FROM plan_templates WHERE id = ?", (template_id,)
    ).fetchone()
    if not template:
        raise RuntimeError("Plantilla de plan no encontrada.")
    start_date = date.fromisoformat(start_date_str)
    template = dict(template)
    plan_name = f"Plan {template['crop_type']}"
    plan_row = db.execute(
        """
        INSERT INTO plans (name, description, targets_json, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            plan_name,
            f"Plan generado desde plantilla {template_id}",
            json.dumps({}),
            utc_now(),
        ),
    )
    plan_id = plan_row.lastrowid
    db.execute(
        """
        INSERT INTO producer_plans (producer_id, plan_id, start_date, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (producer_id, plan_id, start_date_str, "activo", utc_now()),
    )
    tasks = build_tasks_from_template(dict(template), start_date)
    now = utc_now()
    for task in tasks:
        db.execute(
            """
            INSERT INTO producer_tasks (
                producer_id, template_id, task_name, order_sequence, status,
                estimated_date, completion_date, progress_pct, blocker_reason,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                producer_id,
                template_id,
                task["task_name"],
                task["order_sequence"],
                "PENDIENTE",
                task["estimated_date"],
                None,
                None,
                None,
                now,
                now,
            ),
        )
    db.commit()
    return int(plan_id)


def update_task_status(
    task_id: int,
    status: str,
    progress_pct: int | None,
    blocker_reason: str | None,
) -> None:
    db = get_db()
    task = db.execute(
        "SELECT * FROM producer_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not task:
        raise RuntimeError("Tarea no encontrada.")
    task = dict(task)
    completion_date = task.get("completion_date")
    today_str = date.today().isoformat()
    if status == "COMPLETADO":
        completion_date = today_str
    db.execute(
        """
        UPDATE producer_tasks
        SET status = ?, progress_pct = ?, blocker_reason = ?, completion_date = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, progress_pct, blocker_reason, completion_date, utc_now(), task_id),
    )

    if status == "COMPLETADO" and task.get("estimated_date"):
        try:
            estimated = date.fromisoformat(task["estimated_date"])
            completed = date.fromisoformat(completion_date)
        except ValueError:
            estimated = None
            completed = None
        if estimated and completed:
            delay_days = (completed - estimated).days
            if delay_days != 0:
                db.execute(
                    """
                    UPDATE producer_tasks
                    SET estimated_date = date(estimated_date, ? || ' days'),
                        updated_at = ?
                    WHERE producer_id = ?
                      AND template_id = ?
                      AND order_sequence > ?
                    """,
                    (
                        delay_days,
                        utc_now(),
                        task["producer_id"],
                        task["template_id"],
                        task["order_sequence"],
                    ),
                )
    db.commit()


def get_active_plan(producer_id: int) -> dict[str, Any] | None:
    db = get_db()
    row = db.execute(
        """
        SELECT producer_plans.id AS assignment_id,
               producer_plans.start_date,
               producer_plans.status,
               plans.id AS plan_id,
               plans.name,
               plans.description,
               plans.targets_json
        FROM producer_plans
        JOIN plans ON plans.id = producer_plans.plan_id
        WHERE producer_plans.producer_id = ?
          AND producer_plans.status = 'activo'
        ORDER BY producer_plans.start_date DESC
        LIMIT 1
        """,
        (producer_id,),
    ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["targets"] = json.loads(data.pop("targets_json") or "{}")
    return data


def recent_daily_logs(producer_id: int, limit: int = 3) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, plan_id, log_date, notes, metrics_json, created_at
        FROM daily_logs
        WHERE producer_id = ?
        ORDER BY log_date DESC, created_at DESC
        LIMIT ?
        """,
        (producer_id, limit),
    ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["metrics"] = json.loads(item.pop("metrics_json") or "{}")
        results.append(item)
    return results


def save_daily_log(
    producer_id: int,
    plan_id: int | None,
    log_type_id: int | None,
    log_date: str,
    notes: str,
    metrics: dict[str, Any],
) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO daily_logs (
            producer_id, plan_id, log_type_id, log_date, notes, metrics_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            producer_id,
            plan_id,
            log_type_id,
            log_date,
            notes,
            json.dumps(metrics),
            utc_now(),
        ),
    )
    db.execute(
        "UPDATE producers SET last_checkin_date = ? WHERE id = ?",
        (log_date, producer_id),
    )
    db.commit()


def evaluate_plan_progress(
    plan: dict[str, Any] | None,
    logs: list[dict[str, Any]],
) -> dict[str, Any]:
    if not plan or not logs:
        return {"status": "sin_datos", "flags": [], "summary": None}
    targets = plan.get("targets", {})
    latest = logs[0]
    metrics = latest.get("metrics", {})
    flags: list[str] = []
    for key, expected in targets.items():
        actual = metrics.get(key)
        if actual is None:
            flags.append(f"falta_{key}")
            continue
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if actual < expected:
                flags.append(f"{key}_bajo")
        elif actual != expected:
            flags.append(f"{key}_fuera_de_objetivo")
    status = "ok" if not flags else "atencion"
    summary = {
        "log_date": latest.get("log_date"),
        "observaciones": flags,
    }
    return {"status": status, "flags": flags, "summary": summary}


def should_prompt_daily_checkin(producer: dict[str, Any]) -> bool:
    tz_name = producer.get("timezone") or DEFAULT_TIMEZONE
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(DEFAULT_TIMEZONE)
    now = datetime.now(tz)
    today_str = now.date().isoformat()
    last_checkin = producer.get("last_checkin_date")
    if last_checkin == today_str:
        return False
    return now.hour >= DAILY_CHECKIN_HOUR


def recent_chat(producer_id: int, limit: int = 6) -> list[str]:
    db = get_db()
    rows = db.execute(
        """
        SELECT direction, content FROM messages
        WHERE producer_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (producer_id, limit),
    ).fetchall()
    items = list(reversed(rows))
    return [f'{row["direction"]}: {row["content"]}' for row in items]


def build_context(role: str, phone: str, last_user_message: str) -> dict[str, Any]:
    producer = get_or_create_producer(phone)
    form_state = get_or_create_form(producer["id"])
    active_plan = get_active_plan(producer["id"])
    logs = recent_daily_logs(producer["id"])
    plan_evaluation = evaluate_plan_progress(active_plan, logs)
    context: dict[str, Any] = {
        "role": role,
        "producer": producer,
        "form_state": form_state,
        "recent_chat": recent_chat(producer["id"]),
        "active_task": get_active_task(producer["id"]),
        "daily_logs": logs,
        "active_plan": active_plan,
        "plan_evaluation": plan_evaluation,
        "daily_prompt_needed": should_prompt_daily_checkin(producer),
        "weekly_summary": None,
        "last_user_message": last_user_message,
    }

    if role == "consulta":
        context["weekly_summary"] = "7d: sin datos suficientes registrados."
    if role == "intervencion":
        context["recent_chat"] = []
        context["weekly_summary"] = "7d: sin datos suficientes registrados."

    return context


def run_mml(role: str, context: dict[str, Any]) -> dict[str, Any]:
    agent_config = get_agent_config(role)
    system_prompt = agent_config["prompt"]
    llm = get_local_llm()
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        temperature=0.2,
        max_tokens=agent_config["max_tokens"],
    )
    content = response["choices"][0]["message"]["content"] or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Respuesta inválida desde el modelo local.") from exc


_LOCAL_LLM: Llama | None = None


def get_local_llm() -> Llama:
    global _LOCAL_LLM
    if _LOCAL_LLM is None:
        if not Path(LOCAL_MODEL_PATH).exists():
            raise RuntimeError(
                f"No se encontró el modelo local en {LOCAL_MODEL_PATH}."
            )
        _LOCAL_LLM = Llama(
            model_path=LOCAL_MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
        )
    return _LOCAL_LLM


def get_agent_config(role: str) -> dict[str, Any]:
    db = get_db()
    row = db.execute("SELECT * FROM agent_configs WHERE role = ?", (role,)).fetchone()
    if row:
        return dict(row)
    return {"role": role, "enabled": 1, "prompt": PROMPTS[role], "max_tokens": 300}


def apply_model_actions(phone: str, model_output: dict[str, Any]) -> dict[str, Any]:
    producer = get_or_create_producer(phone)
    form = get_or_create_form(producer["id"])
    actions = model_output.get("acciones", {})
    updates = actions.get("actualizar_formulario", {})
    if updates:
        db = get_db()
        valid = {
            "cultivo": updates.get("cultivo"),
            "sintoma": updates.get("sintoma"),
            "inicio_problema": updates.get("inicio_problema"),
            "foto_recibida": updates.get("foto_recibida"),
        }
        for key, value in valid.items():
            if value is not None:
                form[key] = value
        db.execute(
            """
            UPDATE forms
            SET cultivo = ?, sintoma = ?, inicio_problema = ?, foto_recibida = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                form.get("cultivo"),
                form.get("sintoma"),
                form.get("inicio_problema"),
                int(bool(form.get("foto_recibida"))),
                utc_now(),
                form["id"],
            ),
        )
        db.commit()
    alert = actions.get("alerta")
    if alert:
        db = get_db()
        db.execute(
            """
            INSERT INTO alerts (producer_id, level, reason, action, message, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                producer["id"],
                alert.get("nivel", "medio"),
                alert.get("motivo", "sin motivo"),
                alert.get("accion_recomendada", "sin accion"),
                model_output.get("respuesta_chat", ""),
                "abierta",
                utc_now(),
            ),
        )
        db.commit()
    bitacora = actions.get("bitacora")
    if bitacora:
        plan = get_active_plan(producer["id"])
        log_date = bitacora.get("fecha") or date.today().isoformat()
        notes = bitacora.get("notas") or ""
        metrics = bitacora.get("metricas") or {}
        log_type_id = bitacora.get("log_type_id")
        save_daily_log(
            producer_id=producer["id"],
            plan_id=plan["plan_id"] if plan else None,
            log_type_id=int(log_type_id) if log_type_id else None,
            log_date=log_date,
            notes=notes,
            metrics=metrics,
        )
    tarea = actions.get("actualizar_tarea")
    if tarea:
        status = tarea.get("status")
        task_id = tarea.get("task_id")
        if not task_id or not status:
            raise RuntimeError("actualizar_tarea requiere task_id y status.")
        update_task_status(
            task_id=int(task_id),
            status=str(status),
            progress_pct=tarea.get("avance"),
            blocker_reason=tarea.get("motivo"),
        )
    return model_output


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "time": utc_now()})


@app.post("/agent")
def agent() -> Any:
    payload = request.get_json(force=True)
    role = payload.get("role")
    phone = payload.get("phone")
    message = payload.get("message", "")

    if not phone:
        return jsonify({"error": "phone requerido"}), 400

    producer = get_or_create_producer(phone)
    role = role or producer.get("assigned_role") or "formulario"
    if role not in PROMPTS:
        return jsonify({"error": "role invalido"}), 400

    db = get_db()
    db.execute(
        """
        INSERT INTO messages (producer_id, direction, content, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (producer["id"], "usuario", message, "recibido", utc_now()),
    )
    db.commit()

    context = build_context(role, phone, message)
    agent_config = get_agent_config(role)
    if not producer.get("allowed"):
        return jsonify({"error": "productor no autorizado"}), 403
    if producer.get("status") != "activo":
        return jsonify({"error": "productor inactivo"}), 403
    if not agent_config.get("enabled"):
        return jsonify({"error": f"agente {role} desactivado"}), 403
    if role == "formulario" and not producer.get("enable_formulario"):
        return jsonify({"error": "agente formulario desactivado"}), 403
    if role == "consulta" and not producer.get("enable_consulta"):
        return jsonify({"error": "agente consulta desactivado"}), 403
    if role == "intervencion" and not producer.get("enable_intervencion"):
        return jsonify({"error": "agente intervencion desactivado"}), 403

    model_output = run_mml(role, context)
    model_output = apply_model_actions(phone, model_output)

    db.execute(
        """
        INSERT INTO messages (producer_id, direction, content, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (producer["id"], "asistente", model_output["respuesta_chat"], "enviado", utc_now()),
    )
    db.commit()

    return jsonify({"context": context, "model_output": model_output})


@app.post("/form/update")
def update_form() -> Any:
    payload = request.get_json(force=True)
    phone = payload.get("phone")
    updates = payload.get("updates", {})

    if not phone:
        return jsonify({"error": "phone requerido"}), 400

    producer = get_or_create_producer(phone)
    form = get_or_create_form(producer["id"])
    for key, value in updates.items():
        if value is not None:
            form[key] = value
    db = get_db()
    db.execute(
        """
        UPDATE forms
        SET cultivo = ?, sintoma = ?, inicio_problema = ?, foto_recibida = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            form.get("cultivo"),
            form.get("sintoma"),
            form.get("inicio_problema"),
            int(bool(form.get("foto_recibida"))),
            utc_now(),
            form["id"],
        ),
    )
    db.commit()
    return jsonify({"status": "ok", "form_state": form})


@app.post("/alert")
def create_alert() -> Any:
    payload = request.get_json(force=True)
    phone = payload.get("phone")
    alert = payload.get("alert")

    if not phone or not alert:
        return jsonify({"error": "phone y alert requeridos"}), 400

    producer = get_or_create_producer(phone)
    db = get_db()
    db.execute(
        """
        INSERT INTO alerts (producer_id, level, reason, action, message, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            producer["id"],
            alert.get("nivel", "medio"),
            alert.get("motivo", "sin motivo"),
            alert.get("accion_recomendada", "sin accion"),
            alert.get("mensaje", ""),
            "abierta",
            utc_now(),
        ),
    )
    db.commit()
    return jsonify({"status": "ok"})


@app.post("/plans/templates")
def create_plan_template() -> Any:
    payload = request.get_json(force=True)
    crop_type = payload.get("crop_type")
    tasks = payload.get("tasks")
    if not crop_type or not isinstance(tasks, list):
        return jsonify({"error": "crop_type y tasks requeridos"}), 400
    db = get_db()
    db.execute(
        """
        INSERT INTO plan_templates (crop_type, tasks_json, created_at)
        VALUES (?, ?, ?)
        """,
        (crop_type, json.dumps(tasks), utc_now()),
    )
    db.commit()
    return jsonify({"status": "ok"})


@app.post("/plans/assign")
def assign_plan() -> Any:
    payload = request.get_json(force=True)
    phone = payload.get("phone")
    producer_id = payload.get("producer_id")
    template_id = payload.get("template_id")
    start_date_str = payload.get("start_date")
    if not template_id or not start_date_str:
        return jsonify({"error": "template_id y start_date requeridos"}), 400
    if not producer_id and not phone:
        return jsonify({"error": "producer_id o phone requerido"}), 400
    producer = get_or_create_producer(phone) if phone else None
    if producer_id:
        db = get_db()
        row = db.execute(
            "SELECT * FROM producers WHERE id = ?", (producer_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "producer_id invalido"}), 404
        producer = dict(row)
    if not producer:
        return jsonify({"error": "productor no encontrado"}), 404
    assign_plan_to_producer(producer["id"], int(template_id), start_date_str)
    return jsonify({"status": "ok"})


@app.get("/alerts/pending")
def alerts_pending() -> Any:
    db = get_db()
    rows = db.execute(
        """
        SELECT alerts.id, alerts.message, alerts.level, alerts.reason, alerts.action,
               producers.phone
        FROM alerts
        JOIN producers ON producers.id = alerts.producer_id
        WHERE alerts.status = 'abierta' AND alerts.sent_at IS NULL
        ORDER BY alerts.created_at ASC
        """
    ).fetchall()
    return jsonify({"alerts": [dict(row) for row in rows]})


@app.post("/alerts/<int:alert_id>/sent")
def alert_mark_sent(alert_id: int) -> Any:
    db = get_db()
    db.execute(
        "UPDATE alerts SET sent_at = ?, status = 'enviada' WHERE id = ?",
        (utc_now(), alert_id),
    )
    db.commit()
    return jsonify({"status": "ok"})


@app.get("/admin")
def admin_dashboard() -> Any:
    db = get_db()
    counts = {
        "producers": db.execute("SELECT COUNT(*) FROM producers").fetchone()[0],
        "forms": db.execute("SELECT COUNT(*) FROM forms").fetchone()[0],
        "alerts": db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0],
        "messages": db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
    }
    return render_template("dashboard.html", counts=counts)


@app.get("/admin/producers")
def admin_producers() -> Any:
    db = get_db()
    rows = db.execute("SELECT * FROM producers ORDER BY created_at DESC").fetchall()
    return render_template("producers.html", producers=rows)


@app.get("/admin/producers/new")
def admin_producer_new() -> Any:
    return render_template("producer_new.html")


@app.post("/admin/producers")
def admin_producer_create() -> Any:
    phone = request.form.get("phone", "").strip()
    name = request.form.get("name", "").strip() or None
    zone = request.form.get("zone", "").strip() or None
    timezone = request.form.get("timezone", "").strip() or DEFAULT_TIMEZONE
    status = request.form.get("status", "activo")
    allowed = 1 if request.form.get("allowed") == "on" else 0
    assigned_role = request.form.get("assigned_role") or None
    now = utc_now()
    db = get_db()
    db.execute(
        """
        INSERT INTO producers (
            phone, name, zone, preferred_language, main_crops, allowed, status, timezone,
            assigned_role, enable_formulario, enable_consulta, enable_intervencion, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            phone,
            name,
            zone,
            "es",
            json.dumps([]),
            allowed,
            status,
            timezone,
            assigned_role,
            1,
            1,
            1,
            now,
        ),
    )
    db.commit()
    return redirect(url_for("admin_producers"))


@app.get("/admin/producers/<int:producer_id>")
def admin_producer_detail(producer_id: int) -> Any:
    db = get_db()
    producer = db.execute(
        "SELECT * FROM producers WHERE id = ?", (producer_id,)
    ).fetchone()
    templates = db.execute(
        "SELECT * FROM plan_templates ORDER BY created_at DESC"
    ).fetchall()
    tasks = db.execute(
        """
        SELECT * FROM producer_tasks
        WHERE producer_id = ?
        ORDER BY order_sequence ASC
        """,
        (producer_id,),
    ).fetchall()
    daily_logs = db.execute(
        """
        SELECT daily_logs.*, log_types.name AS log_type_name
        FROM daily_logs
        LEFT JOIN log_types ON log_types.id = daily_logs.log_type_id
        WHERE daily_logs.producer_id = ?
        ORDER BY daily_logs.log_date DESC, daily_logs.created_at DESC
        LIMIT 20
        """,
        (producer_id,),
    ).fetchall()
    forms = db.execute(
        "SELECT * FROM forms WHERE producer_id = ? ORDER BY created_at DESC",
        (producer_id,),
    ).fetchall()
    alerts = db.execute(
        "SELECT * FROM alerts WHERE producer_id = ? ORDER BY created_at DESC",
        (producer_id,),
    ).fetchall()
    messages = db.execute(
        """
        SELECT direction, content, created_at
        FROM messages
        WHERE producer_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (producer_id,),
    ).fetchall()
    return render_template(
        "producer_detail.html",
        producer=producer,
        templates=templates,
        tasks=tasks,
        daily_logs=daily_logs,
        forms=forms,
        alerts=alerts,
        messages=messages,
    )


@app.post("/admin/producers/<int:producer_id>/update")
def admin_producer_update(producer_id: int) -> Any:
    name = request.form.get("name", "").strip() or None
    zone = request.form.get("zone", "").strip() or None
    timezone = request.form.get("timezone", "").strip() or DEFAULT_TIMEZONE
    allowed = 1 if request.form.get("allowed") == "on" else 0
    status = request.form.get("status", "activo")
    assigned_role = request.form.get("assigned_role") or None
    enable_formulario = 1 if request.form.get("enable_formulario") == "on" else 0
    enable_consulta = 1 if request.form.get("enable_consulta") == "on" else 0
    enable_intervencion = 1 if request.form.get("enable_intervencion") == "on" else 0
    db = get_db()
    db.execute(
        """
        UPDATE producers
        SET name = ?, zone = ?, timezone = ?, status = ?, allowed = ?, assigned_role = ?,
            enable_formulario = ?, enable_consulta = ?, enable_intervencion = ?
        WHERE id = ?
        """,
        (
            name,
            zone,
            timezone,
            status,
            allowed,
            assigned_role,
            enable_formulario,
            enable_consulta,
            enable_intervencion,
            producer_id,
        ),
    )
    db.commit()
    return redirect(url_for("admin_producer_detail", producer_id=producer_id))


@app.post("/admin/forms/new")
def admin_form_create() -> Any:
    producer_id = int(request.form.get("producer_id"))
    now = utc_now()
    db = get_db()
    db.execute(
        """
        INSERT INTO forms (producer_id, status, cultivo, sintoma, inicio_problema, foto_recibida, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (producer_id, "abierto", None, None, None, 0, now, now),
    )
    db.commit()
    return redirect(url_for("admin_producer_detail", producer_id=producer_id))


@app.get("/admin/plans")
def admin_plans() -> Any:
    db = get_db()
    templates = db.execute(
        "SELECT * FROM plan_templates ORDER BY created_at DESC"
    ).fetchall()
    producers = db.execute(
        "SELECT id, name, phone FROM producers ORDER BY created_at DESC"
    ).fetchall()
    return render_template("plans.html", templates=templates, producers=producers)


@app.get("/admin/plans/new")
def admin_plan_new() -> Any:
    return render_template("plan_new.html")


@app.post("/admin/plans")
def admin_plan_create() -> Any:
    crop_type = request.form.get("crop_type", "").strip()
    tasks_json = request.form.get("tasks_json", "").strip()
    if not crop_type or not tasks_json:
        return redirect(url_for("admin_plan_new"))
    db = get_db()
    db.execute(
        """
        INSERT INTO plan_templates (crop_type, tasks_json, created_at)
        VALUES (?, ?, ?)
        """,
        (crop_type, tasks_json, utc_now()),
    )
    db.commit()
    return redirect(url_for("admin_plans"))


@app.get("/admin/plans/<int:template_id>")
def admin_plan_detail(template_id: int) -> Any:
    db = get_db()
    template = db.execute(
        "SELECT * FROM plan_templates WHERE id = ?", (template_id,)
    ).fetchone()
    return render_template("plan_detail.html", template=template)


@app.post("/admin/plans/<int:template_id>/update")
def admin_plan_update(template_id: int) -> Any:
    crop_type = request.form.get("crop_type", "").strip()
    tasks_json = request.form.get("tasks_json", "").strip()
    db = get_db()
    db.execute(
        """
        UPDATE plan_templates
        SET crop_type = ?, tasks_json = ?
        WHERE id = ?
        """,
        (crop_type, tasks_json, template_id),
    )
    db.commit()
    return redirect(url_for("admin_plan_detail", template_id=template_id))


@app.post("/admin/plans/assign")
def admin_plan_assign() -> Any:
    template_id = request.form.get("template_id")
    start_date = request.form.get("start_date")
    producer_ids = request.form.getlist("producer_ids")
    single_producer_id = request.form.get("producer_id")
    if single_producer_id:
        producer_ids.append(single_producer_id)
    if not template_id or not start_date or not producer_ids:
        return redirect(url_for("admin_plans"))
    for producer_id in producer_ids:
        assign_plan_to_producer(int(producer_id), int(template_id), start_date)
    return redirect(url_for("admin_plans"))


@app.get("/admin/log-types")
def admin_log_types() -> Any:
    db = get_db()
    rows = db.execute("SELECT * FROM log_types ORDER BY created_at DESC").fetchall()
    return render_template("log_types.html", log_types=rows)


@app.get("/admin/log-types/new")
def admin_log_type_new() -> Any:
    return render_template("log_type_new.html")


@app.post("/admin/log-types")
def admin_log_type_create() -> Any:
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not name:
        return redirect(url_for("admin_log_type_new"))
    db = get_db()
    db.execute(
        """
        INSERT INTO log_types (name, description, created_at)
        VALUES (?, ?, ?)
        """,
        (name, description, utc_now()),
    )
    db.commit()
    return redirect(url_for("admin_log_types"))


@app.get("/admin/log-types/<int:log_type_id>")
def admin_log_type_detail(log_type_id: int) -> Any:
    db = get_db()
    log_type = db.execute(
        "SELECT * FROM log_types WHERE id = ?", (log_type_id,)
    ).fetchone()
    return render_template("log_type_detail.html", log_type=log_type)


@app.post("/admin/log-types/<int:log_type_id>/update")
def admin_log_type_update(log_type_id: int) -> Any:
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    db = get_db()
    db.execute(
        """
        UPDATE log_types
        SET name = ?, description = ?
        WHERE id = ?
        """,
        (name, description, log_type_id),
    )
    db.commit()
    return redirect(url_for("admin_log_type_detail", log_type_id=log_type_id))


@app.get("/admin/producers/<int:producer_id>/tasks")
def admin_producer_tasks(producer_id: int) -> Any:
    db = get_db()
    producer = db.execute(
        "SELECT * FROM producers WHERE id = ?", (producer_id,)
    ).fetchone()
    tasks = db.execute(
        """
        SELECT * FROM producer_tasks
        WHERE producer_id = ?
        ORDER BY order_sequence ASC
        """,
        (producer_id,),
    ).fetchall()
    return render_template(
        "producer_tasks.html", producer=producer, tasks=tasks
    )


@app.post("/admin/tasks/<int:task_id>/update")
def admin_task_update(task_id: int) -> Any:
    status = request.form.get("status", "PENDIENTE")
    progress = request.form.get("progress_pct")
    blocker_reason = request.form.get("blocker_reason") or None
    progress_pct = int(progress) if progress else None
    update_task_status(task_id, status, progress_pct, blocker_reason)
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.get("/admin/producers/<int:producer_id>/daily-logs")
def admin_daily_logs(producer_id: int) -> Any:
    db = get_db()
    producer = db.execute(
        "SELECT * FROM producers WHERE id = ?", (producer_id,)
    ).fetchone()
    logs = db.execute(
        """
        SELECT daily_logs.*, log_types.name AS log_type_name
        FROM daily_logs
        LEFT JOIN log_types ON log_types.id = daily_logs.log_type_id
        WHERE daily_logs.producer_id = ?
        ORDER BY daily_logs.log_date DESC, daily_logs.created_at DESC
        """,
        (producer_id,),
    ).fetchall()
    log_types = db.execute(
        "SELECT * FROM log_types ORDER BY name"
    ).fetchall()
    return render_template(
        "daily_logs.html",
        producer=producer,
        daily_logs=logs,
        log_types=log_types,
    )


@app.get("/admin/daily-logs/<int:log_id>")
def admin_daily_log_detail(log_id: int) -> Any:
    db = get_db()
    log = db.execute(
        """
        SELECT daily_logs.*, log_types.name AS log_type_name
        FROM daily_logs
        LEFT JOIN log_types ON log_types.id = daily_logs.log_type_id
        WHERE daily_logs.id = ?
        """,
        (log_id,),
    ).fetchone()
    log_types = db.execute(
        "SELECT * FROM log_types ORDER BY name"
    ).fetchall()
    return render_template(
        "daily_log_detail.html", log=log, log_types=log_types
    )


@app.post("/admin/daily-logs/<int:log_id>/update")
def admin_daily_log_update(log_id: int) -> Any:
    log_date = request.form.get("log_date")
    notes = request.form.get("notes", "")
    metrics_json = request.form.get("metrics_json", "{}")
    log_type_id = request.form.get("log_type_id") or None
    db = get_db()
    db.execute(
        """
        UPDATE daily_logs
        SET log_date = ?, notes = ?, metrics_json = ?, log_type_id = ?
        WHERE id = ?
        """,
        (
            log_date,
            notes,
            metrics_json,
            int(log_type_id) if log_type_id else None,
            log_id,
        ),
    )
    db.commit()
    return redirect(url_for("admin_daily_log_detail", log_id=log_id))


@app.get("/admin/agents")
def admin_agents() -> Any:
    db = get_db()
    rows = db.execute("SELECT * FROM agent_configs ORDER BY role").fetchall()
    return render_template("agents.html", agents=rows)


@app.post("/admin/agents/<role>")
def admin_agents_update(role: str) -> Any:
    db = get_db()
    enabled = 1 if request.form.get("enabled") == "on" else 0
    prompt = request.form.get("prompt", "").strip() or PROMPTS.get(role, "")
    max_tokens = int(request.form.get("max_tokens", 300))
    db.execute(
        """
        UPDATE agent_configs
        SET enabled = ?, prompt = ?, max_tokens = ?
        WHERE role = ?
        """,
        (enabled, prompt, max_tokens, role),
    )
    db.commit()
    return redirect(url_for("admin_agents"))


@app.get("/admin/forms")
def admin_forms() -> Any:
    db = get_db()
    rows = db.execute(
        """
        SELECT forms.*, producers.phone
        FROM forms
        JOIN producers ON producers.id = forms.producer_id
        ORDER BY forms.created_at DESC
        """
    ).fetchall()
    return render_template("forms.html", forms=rows)


@app.get("/admin/forms/<int:form_id>")
def admin_form_detail(form_id: int) -> Any:
    db = get_db()
    row = db.execute(
        """
        SELECT forms.*, producers.phone
        FROM forms
        JOIN producers ON producers.id = forms.producer_id
        WHERE forms.id = ?
        """,
        (form_id,),
    ).fetchone()
    return render_template("form_detail.html", form=row)


@app.post("/admin/forms/<int:form_id>/status")
def admin_form_status(form_id: int) -> Any:
    status = request.form.get("status", "abierto")
    db = get_db()
    db.execute(
        "UPDATE forms SET status = ?, updated_at = ? WHERE id = ?",
        (status, utc_now(), form_id),
    )
    db.commit()
    return redirect(url_for("admin_form_detail", form_id=form_id))


@app.get("/admin/alerts")
def admin_alerts() -> Any:
    db = get_db()
    rows = db.execute(
        """
        SELECT alerts.*, producers.phone
        FROM alerts
        JOIN producers ON producers.id = alerts.producer_id
        ORDER BY alerts.created_at DESC
        """
    ).fetchall()
    return render_template("alerts.html", alerts=rows)


@app.get("/admin/alerts/<int:alert_id>")
def admin_alert_detail(alert_id: int) -> Any:
    db = get_db()
    row = db.execute(
        """
        SELECT alerts.*, producers.phone
        FROM alerts
        JOIN producers ON producers.id = alerts.producer_id
        WHERE alerts.id = ?
        """,
        (alert_id,),
    ).fetchone()
    return render_template("alert_detail.html", alert=row)


@app.post("/admin/alerts/<int:alert_id>/status")
def admin_alert_status(alert_id: int) -> Any:
    status = request.form.get("status", "abierta")
    db = get_db()
    db.execute("UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id))
    db.commit()
    return redirect(url_for("admin_alert_detail", alert_id=alert_id))


@app.teardown_appcontext
def close_db(exception: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    init_db()
    migrate_db()
    with app.app_context():
        ensure_agent_defaults()
    app.run(host="0.0.0.0", port=5000, debug=True)
