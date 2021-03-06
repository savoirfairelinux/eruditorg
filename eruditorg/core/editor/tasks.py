# -*- coding: utf-8 -*-

import datetime as dt

from celery import shared_task
from django.utils import timezone as tz

from core.email import Email

from .conf import settings as editor_settings
from .models import IssueSubmission
from .shortcuts import get_production_team_group


def _handle_issuesubmission_files_removal():
    now_dt = tz.now()

    # First, fetches the issue submissions whose files must be deleted.
    deletion_limit_dt = now_dt - dt.timedelta(days=editor_settings.ARCHIVE_DAY_OFFSET)
    deletion_limit_dt_range = [
        deletion_limit_dt.replace(hour=0, minute=0, second=0, microsecond=0),
        deletion_limit_dt.replace(hour=23, minute=59, second=59, microsecond=999999),
    ]
    issue_submissions_to_remove = IssueSubmission.objects.filter(
        status=IssueSubmission.VALID, date_modified__range=deletion_limit_dt_range)
    for issue in issue_submissions_to_remove:
        for fversion in issue.files_versions.all():
            [rf.delete() for rf in fversion.submissions.all()]
        issue.archived = True
        issue.save()

    # Fetches the production team group
    production_team = get_production_team_group()
    if production_team is None:
        return

    # Now fetches the issue submissions that will soon be deleted. The production team must be
    # informed that the deletion will occur in a few days.
    email_limit_dt = now_dt - dt.timedelta(days=editor_settings.ARCHIVE_DAY_OFFSET - 5)
    email_limit_dt_range = [
        email_limit_dt.replace(hour=0, minute=0, second=0, microsecond=0),
        email_limit_dt.replace(hour=23, minute=59, second=59, microsecond=999999),
    ]
    issue_submissions_to_email = IssueSubmission.objects.filter(
        status=IssueSubmission.VALID, date_modified__range=email_limit_dt_range)
    if issue_submissions_to_email.exists():
        emails = production_team.user_set.values_list('email', flat=True)
        if not emails:
            return

        email = Email(
            list(emails),
            html_template='emails/editor/issue_files_deletion_content.html',
            subject_template='emails/editor/issue_files_deletion_subject.html',
            extra_context={'issue_submissions': issue_submissions_to_email})
        email.send()


handle_issuesubmission_files_removal = shared_task(_handle_issuesubmission_files_removal)
