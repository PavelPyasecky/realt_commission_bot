class InputError(Exception):
    default_detail = 'Only digits are allowed.'


class CRMError(Exception):
    pass


class LeadNotFoundError(CRMError):
    pass
