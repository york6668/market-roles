"""Build temporary recovery scenarios from core test constructors, never snapshots."""
import json
from pathlib import Path


def build(destination):
    from test_market_state import RevisionFivePublicationTests
    from test_workflow_delivery import WorkflowDeliveryTests
    from v4 import delivery
    from v4.common import read

    market = RevisionFivePublicationTests()
    market.setUp()
    transport = None
    try:
        market.f.draft['outlook']['dispute_zones'] = []
        market.public['outlook']['dispute_zones'] = []
        market.c.d.bind()
        _, _, current = market.adopted()
        transport = WorkflowDeliveryTests()
        transport.setUp()
        delivered = transport.queue()
        transport.begin(delivered)
        delivery.transition(transport.root, delivered, 'CONFIRM', transport.receipt(delivered))
        transport.decision = transport.publish(2)
        unknown = transport.queue()
        transport.begin(unknown)
        delivery.transition(transport.root, unknown, 'UNKNOWN')
        transport.decision = transport.publish(3)
        transport.queue()

        value = {'facts': {name: (market.f.project / name).read_text() for name in
                          ('资产配置.md', '操作记录.md', '纠正记录.md')},
                 'decision': current, 'market': market.f.raw,
                 'versions': {}, 'evidence': {}, 'outbox': {}, 'delivery_baselines': {}, 'research': {}}
        for root in (market.f.store, transport.root):
            for path in (root / 'versions').glob('*/decision.json'):
                value['versions'][path.parent.name] = {
                    'decision': read(path), 'views': {p.name: p.read_text() for p in path.parent.iterdir()
                                                     if p.is_file() and p.name != 'decision.json'}}
            for path in (root / 'evidence').glob('*/evidence.json'):
                value['evidence'][path.parent.name] = {'bundle': read(path),
                    'raw': {p.name: read(p) for p in (path.parent / 'raw').glob('*.json')}}
            value['outbox'].update({str(p.relative_to(root)): read(p) for p in (root / 'outbox').rglob('*.json')})
            value['delivery_baselines'].update({p.name: read(p) for p in root.glob('reported*.json')})
            value['research'].update({str(p.relative_to(root)): read(p) for p in (root / 'research').rglob('*.json')})
        Path(destination).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    finally:
        if transport is not None:
            transport.doCleanups()
        market.doCleanups()
