"""Import-level smoke tests for the Channels ASGI wiring.

The model tests do not import the consumer or routing modules, so these guard
against Channels API breakage (e.g. the 2->3 as_asgi() / get_asgi_application()
changes) during the modernization hops.
"""


def test_routing_application_builds():
    from guacozy_server.routing import application

    assert application is not None
    # ProtocolTypeRouter exposes the configured protocols mapping
    assert "websocket" in application.application_mapping
    assert "http" in application.application_mapping


def test_consumer_exposes_as_asgi():
    from guacozy_server.guacdproxy.consumers import GuacamoleConsumer

    # Channels 3 requires consumers to be wired via .as_asgi()
    assert hasattr(GuacamoleConsumer, "as_asgi")
