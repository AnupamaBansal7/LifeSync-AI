import pytest
from app.api.v1.automations import AUTOMATION_TEMPLATES
from app.services.seed_service import DEFAULT_ROLES


def test_seed_default_roles_structure():
    assert len(DEFAULT_ROLES) >= 8
    # Step 2 requirement: Default primary role must be personal
    assert DEFAULT_ROLES[0]["slug"] == "personal"
    assert DEFAULT_ROLES[0]["name"] == "Personal Life & Wellness"

    slugs = [r["slug"] for r in DEFAULT_ROLES]
    assert "personal" in slugs
    assert "student" in slugs
    assert "professional" in slugs
    assert "entrepreneur" in slugs
    assert "manager" in slugs
    assert "freelancer" in slugs
    assert "teacher" in slugs
    assert "homemaker" in slugs
    assert "custom" in slugs

    for r in DEFAULT_ROLES:
        assert len(r["name"]) > 0
        assert len(r["description"]) > 10
        assert isinstance(r["default_modules"], list)
        assert len(r["default_modules"]) > 0


def test_automation_templates_structure():
    assert len(AUTOMATION_TEMPLATES) >= 5
    for tmpl in AUTOMATION_TEMPLATES:
        assert "name" in tmpl
        assert "trigger_type" in tmpl
        assert "action_type" in tmpl
        assert "trigger_config" in tmpl
        assert "action_config" in tmpl
        assert tmpl["trigger_type"] in ["schedule", "task_overdue", "habit_missed", "deadline_approaching"]
        assert tmpl["action_type"] in ["notify", "generate_plan", "reschedule_suggest", "daily_review"]
