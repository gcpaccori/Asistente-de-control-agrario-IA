from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json
import os
import sqlite3
from flask import Flask, g, jsonify, redirect, render_template, request, url_for
from openai import OpenAI, OpenAIError

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

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MML_PROVIDER = os.getenv("MML_PROVIDER", "groq")

PROMPTS = {
    "formulario": (
        "Eres un asistente agrónomo por WhatsApp. Pregunta natural y breve. "
        "Extrae datos para completar el formulario. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log}, "
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
            created_at TEXT NOT NULL,
            FOREIGN KEY (producer_id) REFERENCES producers (id)
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
            phone, name, zone, preferred_language, main_crops, allowed, assigned_role,
            enable_formulario, enable_consulta, enable_intervencion, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (phone, None, None, "es", json.dumps([]), 0, None, 1, 1, 1, now),
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
    context: dict[str, Any] = {
        "role": role,
        "producer": producer,
        "form_state": form_state,
        "recent_chat": recent_chat(producer["id"]),
        "weekly_summary": None,
        "last_user_message": last_user_message,
    }

    if role == "consulta":
        context["weekly_summary"] = "7d: sin datos suficientes registrados."
    if role == "intervencion":
        context["recent_chat"] = []
        context["weekly_summary"] = "7d: sin datos suficientes registrados."

    return context


def call_groq(role: str, context: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY") or os.environ.get("console.groq.com_apikey")
    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY para conectar con Groq.")

    agent_config = get_agent_config(role)
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    try:
        response = client.responses.create(
            input=[
                {"role": "system", "content": agent_config["prompt"]},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            model=GROQ_MODEL,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_output_tokens=agent_config["max_tokens"],
        )
        return json.loads(response.output_text)
    except (json.JSONDecodeError, OpenAIError) as exc:
        raise RuntimeError("Error al conectar con Groq.") from exc


def run_mml(role: str, context: dict[str, Any]) -> dict[str, Any]:
    if MML_PROVIDER != "groq":
        raise RuntimeError("MML_PROVIDER debe ser 'groq' para usar el servicio real.")
    return call_groq(role, context)


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
        "INSERT INTO messages (producer_id, direction, content, created_at) VALUES (?, ?, ?, ?)",
        (producer["id"], "usuario", message, utc_now()),
    )
    db.commit()

    context = build_context(role, phone, message)
    agent_config = get_agent_config(role)
    if not producer.get("allowed"):
        return jsonify({"error": "productor no autorizado"}), 403
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
        "INSERT INTO messages (producer_id, direction, content, created_at) VALUES (?, ?, ?, ?)",
        (producer["id"], "asistente", model_output["respuesta_chat"], utc_now()),
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
    allowed = 1 if request.form.get("allowed") == "on" else 0
    assigned_role = request.form.get("assigned_role") or None
    now = utc_now()
    db = get_db()
    db.execute(
        """
        INSERT INTO producers (
            phone, name, zone, preferred_language, main_crops, allowed, assigned_role,
            enable_formulario, enable_consulta, enable_intervencion, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (phone, name, zone, "es", json.dumps([]), allowed, assigned_role, 1, 1, 1, now),
    )
    db.commit()
    return redirect(url_for("admin_producers"))


@app.get("/admin/producers/<int:producer_id>")
def admin_producer_detail(producer_id: int) -> Any:
    db = get_db()
    producer = db.execute(
        "SELECT * FROM producers WHERE id = ?", (producer_id,)
    ).fetchone()
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
        forms=forms,
        alerts=alerts,
        messages=messages,
    )


@app.post("/admin/producers/<int:producer_id>/update")
def admin_producer_update(producer_id: int) -> Any:
    name = request.form.get("name", "").strip() or None
    zone = request.form.get("zone", "").strip() or None
    allowed = 1 if request.form.get("allowed") == "on" else 0
    assigned_role = request.form.get("assigned_role") or None
    enable_formulario = 1 if request.form.get("enable_formulario") == "on" else 0
    enable_consulta = 1 if request.form.get("enable_consulta") == "on" else 0
    enable_intervencion = 1 if request.form.get("enable_intervencion") == "on" else 0
    db = get_db()
    db.execute(
        """
        UPDATE producers
        SET name = ?, zone = ?, allowed = ?, assigned_role = ?,
            enable_formulario = ?, enable_consulta = ?, enable_intervencion = ?
        WHERE id = ?
        """,
        (
            name,
            zone,
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
