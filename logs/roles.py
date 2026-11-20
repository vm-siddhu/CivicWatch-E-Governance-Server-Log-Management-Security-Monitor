from django.contrib.auth.models import Group, Permission

ROLE_GRANTS = {
    "Super Administrator": {
        "logentry": ["view", "add", "change", "delete"],
        "alert": ["view", "add", "change", "delete"],
        "auditevent": ["view", "add", "change", "delete"],
        "alertconfiguration": ["view", "add", "change", "delete"],
    },
    "System Administrator": {
        "logentry": ["view", "change"],
        "alert": ["view", "change"],
        "auditevent": ["view"],
    },
    "Monitoring Officer": {
        "logentry": ["view"],
        "alert": ["view"],
    },
}

def ensure_roles_exist():
    """Ensure standard RBAC groups and model permissions are configured."""
    for name, model_perms in ROLE_GRANTS.items():
        group, _ = Group.objects.get_or_create(name=name)
        codename_list = [f"{verb}_{model}" for model, verbs in model_perms.items() for verb in verbs]
        perms = Permission.objects.filter(content_type__app_label="logs", codename__in=codename_list)
        if name == "Super Administrator":
            perms = perms | Permission.objects.filter(
                content_type__app_label="auth",
                codename__in=["view_user", "add_user", "change_user", "view_group", "add_group", "change_group"]
            )
        group.permissions.set(perms.distinct())
