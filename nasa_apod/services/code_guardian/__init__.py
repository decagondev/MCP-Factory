"""Code Guardian service plugin.

Exposes :class:`CodeGuardianService`, which satisfies the
:class:`~nasa_apod.services.base.ServicePlugin` protocol and
registers code-analysis tools and resources onto a FastMCP server.

The service is wired in ``nasa_apod.server`` via the
:class:`~nasa_apod.services.registry.ServiceRegistry`.
"""
