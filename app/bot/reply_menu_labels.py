"""Reply keyboard labels that must pass through to calculator/CRM handlers."""


def main_and_crm_menu_texts(_) -> frozenset[str]:
    return frozenset(
        {
            _("Calculate commission"),
            _("CRM"),
            _("Last calculation"),
            _("Favorites"),
            _("Compare scenarios"),
            _("User statistics"),
            _("Admin broadcast"),
            _("Add lead"),
            _("Today leads"),
            _("All leads"),
            _("Archived leads"),
            _("Forwarded lead"),
            _("Back to main menu"),
        }
    )
