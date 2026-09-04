"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("replicas", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("active_deployment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_services_name"),
    )
    op.create_index("ix_services_name", "services", ["name"])

    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ROLLED_BACK", "SUPERSEDED", name="deployment_status", native_enum=False, length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("is_bad_deployment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deployed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_from_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deployments.id"), nullable=True),
    )
    op.create_index("ix_deployments_service_id", "deployments", ["service_id"])

    op.create_foreign_key(
        "fk_services_active_deployment",
        "services",
        "deployments",
        ["active_deployment_id"],
        ["id"],
    )

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "severity",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="severity", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "DETECTED", "INVESTIGATING", "DIAGNOSED", "AWAITING_APPROVAL",
                "REMEDIATING", "VERIFYING", "RESOLVED", "FAILED",
                name="incident_status", native_enum=False, length=30,
            ),
            nullable=False,
            server_default="DETECTED",
        ),
        sa.Column("triggering_deployment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deployments.id"), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_incidents_service_id", "incidents", ["service_id"])
    op.create_index("ix_incidents_status", "incidents", ["status"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("message", sa.String(300), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerts_incident_id", "alerts", ["incident_id"])
    op.create_index("ix_alerts_service_id", "alerts", ["service_id"])

    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("IN_PROGRESS", "COMPLETED", "FAILED", name="investigation_status", native_enum=False, length=20),
            nullable=False,
            server_default="IN_PROGRESS",
        ),
        sa.Column("llm_provider", sa.String(50), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommended_action", sa.String(50), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_investigations_incident_id", "investigations", ["incident_id"])

    op.create_table(
        "agent_tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("called_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_tool_calls_investigation_id", "agent_tool_calls", ["investigation_id"])

    op.create_table(
        "remediation_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column(
            "action_type",
            sa.Enum(
                "ROLLBACK_DEPLOYMENT", "RESTART_SERVICE", "SCALE_SERVICE",
                name="action_type", native_enum=False, length=30,
            ),
            nullable=False,
        ),
        sa.Column(
            "risk_level",
            sa.Enum("LOW", "MEDIUM", "HIGH", name="risk_level", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING_APPROVAL", "APPROVED", "REJECTED", "EXECUTING", "SUCCEEDED", "FAILED",
                name="remediation_status", native_enum=False, length=20,
            ),
            nullable=False,
            server_default="PENDING_APPROVAL",
        ),
        sa.Column("parameters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("idempotency_key", name="uq_remediation_actions_idempotency_key"),
    )
    op.create_index("ix_remediation_actions_incident_id", "remediation_actions", ["incident_id"])
    op.create_index("ix_remediation_actions_status", "remediation_actions", ["status"])

    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "remediation_action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("remediation_actions.id"),
            nullable=False,
        ),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("approved_by", sa.String(200), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("remediation_action_id", name="uq_approvals_remediation_action_id"),
    )

    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column(
            "remediation_action_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remediation_actions.id"), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum("PASSED", "FAILED", "IN_PROGRESS", name="verification_status", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("metrics_before", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metrics_after", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_verifications_incident_id", "verifications", ["incident_id"])

    op.create_table(
        "postmortems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("timeline", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("remediation_summary", sa.Text(), nullable=False),
        sa.Column("recovery_verification", sa.Text(), nullable=False),
        sa.Column("prevention_recommendations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("markdown_report", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("incident_id", name="uq_postmortems_incident_id"),
    )

    op.create_table(
        "metric_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("error_rate", sa.Float(), nullable=False),
        sa.Column("latency_p50_ms", sa.Float(), nullable=False),
        sa.Column("latency_p95_ms", sa.Float(), nullable=False),
        sa.Column("latency_p99_ms", sa.Float(), nullable=False),
    )
    op.create_index("ix_metric_snapshots_service_id", "metric_snapshots", ["service_id"])
    op.create_index("ix_metric_snapshots_timestamp", "metric_snapshots", ["timestamp"])

    op.create_table(
        "log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", name="log_level", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False, server_default="app"),
    )
    op.create_index("ix_log_entries_service_id", "log_entries", ["service_id"])
    op.create_index("ix_log_entries_timestamp", "log_entries", ["timestamp"])
    op.create_index("ix_log_entries_level", "log_entries", ["level"])


def downgrade() -> None:
    op.drop_table("log_entries")
    op.drop_table("metric_snapshots")
    op.drop_table("postmortems")
    op.drop_table("verifications")
    op.drop_table("approvals")
    op.drop_table("remediation_actions")
    op.drop_table("agent_tool_calls")
    op.drop_table("investigations")
    op.drop_table("alerts")
    op.drop_table("incidents")
    op.drop_constraint("fk_services_active_deployment", "services", type_="foreignkey")
    op.drop_table("deployments")
    op.drop_table("services")
