"""Prepare a collector's existing state for the shared Compose deployment.

Run on the collector node after stopping its original writer. No polling,
report enqueue or send happens here. Credentials stay in their existing file.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from role_support import config, snapshot, restore, write_json


def content(path):
    if not path.exists(): return None
    if path.is_dir():
        return {str(p.relative_to(path)):content(p) for p in sorted(path.rglob('*')) if p.is_file()}
    with path.open('rb') as stream: header=stream.read(16)
    if header == b'SQLite format 3\x00':
        with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('collector database integrity failed')
            names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            return {'schema':list(db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')),
                    'version':db.execute('PRAGMA user_version').fetchone()[0],
                    'rows':{n:sorted(db.execute('SELECT * FROM "'+n.replace('"','""')+'"'),key=repr) for n in names}}
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(node_file, destination, compose_file, image_tag):
    value=config(node_file)
    if value['role'] != 'collector': raise ValueError('existing collector configuration required')
    destination=Path(destination).resolve()
    if destination.exists(): raise ValueError('use a new node directory; never replace an existing writer')
    paths=value['state_paths']
    names=[Path(p).name for p in paths.values()]
    if len(set(names)) != len(names): raise ValueError('state filenames collide; preserve separate explicit mounts')
    base=value['environment'].get('STATE_FILE')
    if not base or base not in paths.values(): raise ValueError('STATE_FILE must identify an existing state mapping')
    destination.mkdir(parents=True,mode=0o700)
    snapshot(value,destination/'migration')
    target={**value,'state_paths':{k:str(destination/'data'/Path(p).name) for k,p in paths.items()}}
    restore(destination/'migration',target)
    for key,path in target['state_paths'].items():
        if content(destination/'migration'/key) != content(Path(path)):
            raise ValueError('collector restoration changed '+key)
    replacements={p:'/data/'+Path(p).name for p in paths.values()}
    environment={k:replacements.get(v,v) for k,v in value['environment'].items()}
    # Explicit configured overrides are retained. Defaults in the collector
    # derive from STATE_FILE and keep the same basenames and asset identities.
    for env,key in (('MARKET_HISTORY_DB','market_history'),('BTC_PUSH_DELIVERY_DB','delivery'),
                    ('QQQ_STATE_FILE','qqq'),('VOO_STATE_FILE','voo')):
        if key in paths: environment[env]=replacements[paths[key]]
    environment['BTC_PUSH_LOG_FILE']='/data/collector.log'
    private=value.get('private_environment_file')
    if not private or not Path(private).is_file(): raise ValueError('reuse the actual local credential file')
    if Path(private).stat().st_mode & 0o077: raise ValueError('collector credential permissions must be owner only')
    write_json(destination/'collector.json',{'arguments':value.get('arguments',[]),'environment':environment,
        'private_environment_file':'/run/btc/collector-private.json'})
    env={'BTC_COLLECTOR_DATA_DIR':str(destination/'data'),'BTC_COLLECTOR_CONFIG':str(destination/'collector.json'),
         'BTC_COLLECTOR_PRIVATE_ENV':private,'BTC_IMAGE_TAG':image_tag}
    (destination/'compose.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
    write_json(destination/'handoff.json',{'source_config':str(Path(node_file).resolve()),
        'compose_file':str(Path(compose_file).resolve()),'restored_paths':target['state_paths'],
        'comparison':'EXACT_SQLITE_ROWS_AND_FILE_HASHES','started':False,
        'rollback':'Stop the container and snapshot its latest data; never restore the migration snapshot over newer queues.'})
    return {'prepared':str(destination),'compared_states':len(paths),'started':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',required=True);parser.add_argument('--destination',required=True)
    parser.add_argument('--compose-file',required=True);parser.add_argument('--image-tag',required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.node,args.destination,args.compose_file,args.image_tag)))
