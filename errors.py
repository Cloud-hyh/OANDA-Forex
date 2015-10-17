__author__ = 'zed'


class ApiRequestError(Exception):
    pass


class ApiClientError(Exception):
    pass


class KernelOrderError(Exception):
    pass


class KernelPositionError(Exception):
    pass


class KernelTradeError(Exception):
    pass


class KernelAccountError(Exception):
    pass


class KernelBacktestError(Exception):
    pass

