# Provider adapters

External routing, traffic, tracking, and geocoding services belong here.

The core routing engine must remain provider-independent. An adapter should
implement the `RouteProvider` contract in `logistics.routing` and translate the
provider response into the internal `Route` model.

Build 02 intentionally starts with a deterministic geodesic provider so tests
do not require API keys, network access, or third-party uptime.
