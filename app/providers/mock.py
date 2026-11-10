from app.providers.contracts import ProviderFailure, ProviderProfile, ProviderResult


class MockTransport:
    async def dispatch(self, profile: ProviderProfile, call_id: str, prompt: str) -> ProviderResult:
        return ProviderResult(call_id=call_id, provider_id=profile.provider_id,
                              requested_model_id=profile.model_id, resolved_model_id=profile.model_id,
                              inference_provider="fixed", text="ADAPTER MOCK: respons deterministik, tanpa inferensi model nyata. Pelaksanaan tools dicatat terpisah.",
                              usage={"input_tokens": 0, "output_tokens": 0}, cost_status="KNOWN", actual_cost_idr=0)


MOCK_PROFILE = ProviderProfile(provider_id="mock", model_id="mock-contract-v1", access_tier="FREE_TIER",
                               enabled=True, tools_verified=True, schema_verified=True, tier_verified=True,
                               max_cost_idr=0, price_snapshot="simulation-only-no-provider-charge")


def require_execution_mode(mode: str):
    if mode == "live":
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
    if mode == "replay":
        raise ProviderFailure("REPLAY_NOT_CONFIGURED", cost_idr=0)
