class InvalidAppSignatureError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid or missing app signature")
