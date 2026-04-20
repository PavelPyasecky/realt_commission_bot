"""Reply keyboard labels that must pass through broadcast FSM to other handlers."""


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


def broadcast_submenu_texts(_) -> frozenset[str]:
    return frozenset(
        {
            _("Broadcast list pending"),
            _("Broadcast list failed"),
            _("Broadcast list sent"),
            _("Broadcast new"),
        }
    )


def pass_through_from_broadcast_fsm(_) -> frozenset[str]:
    return main_and_crm_menu_texts(_) | broadcast_submenu_texts(_)
