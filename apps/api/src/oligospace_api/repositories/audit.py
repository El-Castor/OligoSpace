from sqlalchemy import Select, or_, select

from oligospace_api.domain.permissions import Principal
from oligospace_api.models.laboratory import Attachment, ExperimentRun, Validation
from oligospace_api.models.registry import Assay, AuditEvent, Oligo, Project, Target, Team
from oligospace_api.models.scientific import ScientificJob
from oligospace_api.repositories.laboratory import visible_run_query, visible_validation_query
from oligospace_api.repositories.registry import visible_query
from oligospace_api.repositories.scientific import visible_scientific_jobs
from oligospace_api.repositories.workspace import visible_projects_query, visible_teams_query


def visible_own_activity(principal: Principal) -> Select[tuple[AuditEvent]]:
    runs = visible_run_query(principal).with_only_columns(ExperimentRun.id)
    validations = visible_validation_query(principal).with_only_columns(Validation.id)
    attachments = select(Attachment.id).where(
        Attachment.organization_id == principal.organization_id,
        or_(Attachment.experiment_run_id.in_(runs), Attachment.validation_id.in_(validations)),
    )
    return select(AuditEvent).where(
        AuditEvent.actor_id == principal.user_id,
        or_(
            (AuditEvent.entity_type == "oligo")
            & AuditEvent.entity_id.in_(visible_query(Oligo, principal).with_only_columns(Oligo.id)),
            (AuditEvent.entity_type == "target")
            & AuditEvent.entity_id.in_(
                visible_query(Target, principal).with_only_columns(Target.id)
            ),
            (AuditEvent.entity_type == "assay")
            & AuditEvent.entity_id.in_(visible_query(Assay, principal).with_only_columns(Assay.id)),
            AuditEvent.entity_type.in_(("project", "project_membership"))
            & AuditEvent.entity_id.in_(
                visible_projects_query(principal).with_only_columns(Project.id)
            ),
            AuditEvent.entity_type.in_(("team", "team_membership"))
            & AuditEvent.entity_id.in_(visible_teams_query(principal).with_only_columns(Team.id)),
            (AuditEvent.entity_type == "user") & (AuditEvent.entity_id == principal.user_id),
            AuditEvent.entity_type.in_(("organism", "experiment_type")),
            (AuditEvent.entity_type == "experiment_run") & AuditEvent.entity_id.in_(runs),
            (AuditEvent.entity_type == "validation") & AuditEvent.entity_id.in_(validations),
            (AuditEvent.entity_type == "attachment") & AuditEvent.entity_id.in_(attachments),
            (AuditEvent.entity_type == "scientific_job")
            & AuditEvent.entity_id.in_(
                visible_scientific_jobs(principal).with_only_columns(ScientificJob.id)
            ),
        ),
    )
