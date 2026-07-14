"""Domain exceptions module

Custom exceptions for domain layer validation and business rules.
."""


class ValidationException(Exception):
    """Domain validation error

    Raised when business rules or validation constraints are violated.

    Attributes:
        field: Field name that failed validation
        message: Human-readable error message
    ."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on {field}: {message}")


class ProductoYaExisteException(ValidationException):
    """Product already exists

    Raised when attempting to create a product with a duplicate code.
    ."""

    def __init__(self, codigo: str, message: str = "Ya existe un producto con este código"):
        self.codigo = codigo
        super().__init__("codigo", message)


class ProductoNotFoundException(Exception):
    """Product not found

    Raised when attempting to retrieve a non-existent product.

    Attributes:
        codigo: Product code that was not found
    ."""

    def __init__(self, codigo: str, message: str | None = None):
        self.codigo = codigo
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Producto con código '{codigo}' no encontrado")
