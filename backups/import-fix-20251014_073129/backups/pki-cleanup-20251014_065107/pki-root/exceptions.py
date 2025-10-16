"""
PKI Exceptions
Custom exceptions for PKI operations

Alle PKI-spezifischen Fehler und Ausnahmen.
"""


class PKIException(Exception):
    """Base exception for PKI errors"""
    
    def __init__(self, message: str = "PKI operation failed"):
        self.message = message
        super().__init__(self.message)


class CertificateNotFoundError(PKIException):
    """Certificate not found in storage"""
    
    def __init__(self, cert_id: str):
        super().__init__(f"Certificate not found: {cert_id}")
        self.cert_id = cert_id


class CertificateExpiredError(PKIException):
    """Certificate has expired"""
    
    def __init__(self, cert_id: str, expiry_date: str):
        super().__init__(f"Certificate expired: {cert_id} (expired: {expiry_date})")
        self.cert_id = cert_id
        self.expiry_date = expiry_date


class CertificateRevokedError(PKIException):
    """Certificate has been revoked"""
    
    def __init__(self, cert_id: str, revocation_date: str):
        super().__init__(f"Certificate revoked: {cert_id} (revoked: {revocation_date})")
        self.cert_id = cert_id
        self.revocation_date = revocation_date


class InvalidCSRError(PKIException):
    """Invalid Certificate Signing Request"""
    
    def __init__(self, reason: str = "Invalid CSR format"):
        super().__init__(f"Invalid CSR: {reason}")


class CANotInitializedError(PKIException):
    """Certificate Authority not initialized"""
    
    def __init__(self):
        super().__init__("CA not initialized. Call initialize_ca() first.")


class SignatureVerificationError(PKIException):
    """Signature verification failed"""
    
    def __init__(self, reason: str = "Invalid signature"):
        super().__init__(f"Signature verification failed: {reason}")


class InvalidCertificateError(PKIException):
    """Certificate validation failed"""
    
    def __init__(self, reason: str):
        super().__init__(f"Invalid certificate: {reason}")


class KeyGenerationError(PKIException):
    """Key pair generation failed"""
    
    def __init__(self, reason: str = "Key generation failed"):
        super().__init__(f"Key generation error: {reason}")


class EncryptionError(PKIException):
    """Data encryption failed"""
    
    def __init__(self, reason: str = "Encryption failed"):
        super().__init__(f"Encryption error: {reason}")


class DecryptionError(PKIException):
    """Data decryption failed"""
    
    def __init__(self, reason: str = "Decryption failed"):
        super().__init__(f"Decryption error: {reason}")
