from services.synchronization.edge_sync import OfflineQueue

def test_offline_queue_is_durable(tmp_path):
    q = OfflineQueue(tmp_path/'queue.json','edge-1')
    event = q.enqueue({'x':1},'abc')
    assert q.pending()[0]['event_id'] == event.event_id
    q.acknowledge(event.event_id)
    assert q.pending() == []
