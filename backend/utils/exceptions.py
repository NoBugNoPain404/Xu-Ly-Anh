class PipelineError(Exception):
    """Base class for all pipeline-related exceptions."""


class CardNotFoundError(PipelineError):
    """Raised when no valid card polygon is found in a response."""


class RoboflowAPIError(PipelineError):
    """Raised when a Roboflow request fails or returns invalid data."""
