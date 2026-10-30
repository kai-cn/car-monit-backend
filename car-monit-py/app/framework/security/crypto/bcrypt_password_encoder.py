"""BCrypt password encoding.

Not a RuoYi file
----------------
``org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder`` is Spring Security
code. It is ported because ``SecurityUtils.encryptPassword`` / ``matchesPassword`` -- and
therefore every stored ``sys_user.password`` value -- depend on its exact output format.

Compatibility matrix (measured, not assumed)
-------------------------------------------
* Spring's default constructor is ``new BCryptPasswordEncoder()`` -> version ``$2A``,
  strength **10**. Every shipped hash in ``sys_user.password`` therefore looks like
  ``$2a$10$<22-char salt><31-char digest>``.
* ``bcrypt.gensalt(rounds=10, prefix=b"2a")`` produces that exact shape, so hashes
  written by Python are byte-comparable with hashes written by Java and are accepted by
  ``BCryptPasswordEncoder.matches`` in either direction.
* ``bcrypt.checkpw`` (pyca) accepts ``$2a$``, ``$2b$`` and ``$2y$``; Spring's
  ``BCryptPasswordEncoder`` accepts all three as well.

Known divergence -- passwords longer than 72 bytes
-------------------------------------------------
jBCrypt (what Spring uses) cycles the *whole* password through the Blowfish key schedule
and never truncates, while the OpenBSD/pyca implementation truncates at 72 bytes. pyca's
``bcrypt`` ≥ 4.0 refuses such input with ``ValueError`` instead of truncating silently.
The divergence is unreachable through this project's login endpoint (``CommonUtil.checkPassword``
caps the password at 20 characters), so no workaround is attempted -- raising is safer than
silently authenticating against a truncated key.
"""

from __future__ import annotations

import re
from typing import Optional

import bcrypt as _bcrypt

#: Spring: ``private final Pattern BCRYPT_PATTERN = Pattern.compile("\\A\\$2(a|y|b)?\\$(\\d\\d)\\$[./0-9A-Za-z]{53}")``
BCRYPT_PATTERN = re.compile(r"\A\$2(a|y|b)?\$(\d\d)\$[./0-9A-Za-z]{53}")

#: Spring: ``BCryptVersion.$2A`` -> the prefix Java writes.
DEFAULT_VERSION_PREFIX = b"2a"
#: Spring: ``strength`` defaults to 10 (log rounds).
DEFAULT_STRENGTH = 10


class BCryptPasswordEncoder:
    """Java: ``org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder``."""

    def __init__(self, strength: int = DEFAULT_STRENGTH, version_prefix: bytes = DEFAULT_VERSION_PREFIX) -> None:
        self.strength = strength
        self.version_prefix = version_prefix

    # Java: public String encode(CharSequence rawPassword)
    def encode(self, raw_password: Optional[str]) -> str:
        """Hash a password.

        Java throws ``IllegalArgumentException("rawPassword cannot be null")`` -- mirrored.
        """
        if raw_password is None:
            raise ValueError("rawPassword cannot be null")
        salt = _bcrypt.gensalt(rounds=self.strength, prefix=self.version_prefix)
        return _bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("ascii")

    # Java: public boolean matches(CharSequence rawPassword, String encodedPassword)
    def matches(self, raw_password: Optional[str], encoded_password: Optional[str]) -> bool:
        """Verify a password against a stored hash.

        Mirrored defensiveness: Spring logs a warning and returns ``false`` -- it does not
        raise -- when the stored value is null, empty or not BCrypt-shaped. That matters
        because ``sys_user.password`` is nullable and a NULL row would otherwise turn a
        failed login into a 500.
        """
        if raw_password is None:
            raise ValueError("rawPassword cannot be null")
        if not encoded_password:
            # Java: logger.warn("Empty encoded password"); return false;
            return False
        if not BCRYPT_PATTERN.match(encoded_password):
            # Java: logger.warn("Encoded password does not look like BCrypt"); return false;
            return False
        try:
            return _bcrypt.checkpw(raw_password.encode("utf-8"), encoded_password.encode("ascii"))
        except ValueError:
            # Only reachable for a >72-byte presented password (see the module docstring).
            raise

    # Java: public boolean upgradeEncoding(String encodedPassword)
    def upgrade_encoding(self, encoded_password: Optional[str]) -> bool:
        """True when the stored hash uses fewer rounds than this encoder's strength."""
        if not encoded_password:
            return False
        match = BCRYPT_PATTERN.match(encoded_password)
        if not match:
            return False
        return int(match.group(2)) < self.strength


__all__ = ["BCryptPasswordEncoder", "BCRYPT_PATTERN", "DEFAULT_STRENGTH", "DEFAULT_VERSION_PREFIX"]
