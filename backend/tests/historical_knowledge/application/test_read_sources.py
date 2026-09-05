from uuid import uuid7

import pytest
from tests.historical_knowledge.fakes import FakeSourceRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.historical_knowledge.application.read_services.sources import SourceReadService
from roots_of_rhythm.historical_knowledge.domain import Source


@pytest.mark.asyncio
async def test_source_read_service_get_sources_by_ids() -> None:
    source = Source.create("Smithsonian", responsible_organization="SI", source_id=uuid7())
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    service = SourceReadService(fake_transaction_scope(), lambda _t: sources)

    result = await service.get_sources_by_ids({source.id, uuid7()})

    assert result == {source.id: source}
    assert await service.get_sources_by_ids(set()) == {}
