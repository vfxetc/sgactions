import json
import optparse
import sys
import urllib

import yaml
    
from .utils import get_shotgun


FIELD_NAMES = ('id', 'title', 'list_order', 'entity_type', 'selection_required', 'url', 'folder')


def main():
    
    optparser = optparse.OptionParser()
    optparser.add_option('-n', '--dry-run', action="store_true", dest="dry_run")
    optparser.add_option('-l', '--list', action="store_true", dest="list")
    optparser.add_option('-d', '--delete', action="store_true", dest="delete")    
    optparser.add_option('-f', '--force', action="store_true", dest="force")    
    opts, args = optparser.parse_args()
    
    sg = get_shotgun()
    
    # Find and collapse existing.
    existing = {}
    individuals = sg.find('ActionMenuItem', [], FIELD_NAMES)
    for menu_item in individuals:
        if menu_item['url'].startswith('sgaction:'):
            key = menu_item['url'].split('/')[0]

        else:
            key = menu_item['url']
        existing.setdefault(key, []).append(menu_item)
    
    # List the existing menu items.
    if opts.list:
        for key, menu_items in sorted(existing.iteritems(), key=lambda (k, mi): (mi[0]['list_order'], mi[0]['title'])):
            print key
            print '\ttitle: %s' % menu_items[0]['title']
            print '\tlist_order: %s' % menu_items[0]['list_order']
            print '\tentity_types:', ', '.join(str(x['entity_type']) for x in menu_items)
            print '\tids:', ', '.join(str(x['id']) for x in menu_items)
            print '\tselection_required: %s' % menu_items[0]['selection_required']
            print '\trich: %s' % (menu_items[0]['url'].split('/') + [''])[1]
        exit()
    
    # Delete some menu items.
    if opts.delete:
        
        if not args:
            # TODO: Do this with optparse.
            print 'usage: %s --delete <id or entrypoint> [...]' % sys.argv[0]
            exit(1)
            
        for arg in args:
            
            # Delete by ID.
            if arg.isdigit():
                print 'Delete', arg
                if not opts.dry_run:
                    sg.delete('ActionMenuItem', int(arg))
            
            # Delete by URL.
            if arg in existing:
                for menu_item in existing[arg]:
                    print 'Delete', menu_item['id']
                    if not opts.dry_run:
                        sg.delete('ActionMenuItem', menu_item['id'])
        
        exit(0)

    
    # Load the specs.
    specs = {}
    
    if not args:
        # TODO: Do with optparse.
        print 'usage: %s [--reset] actions.yml ...' % sys.argv[0]
        exit(2)
    
    # Get the new ones.
    for path in args:
        for menu_item in yaml.load(open(path).read()):

            if 'entrypoint' in menu_item:
                key = menu_item['entrypoint']
                menu_item['is_sgaction'] = True
            else:
                key = menu_item.get('url')
                menu_item['is_sgaction'] = False

            if not key:
                print 'missing entrypoint and url'
                continue

            if key in specs:
                print 'WARNING: collision on', key
            specs[key] = menu_item
            menu_item.setdefault('title', key)
            menu_item.setdefault('folder', None)
            menu_item.setdefault('list_order', None)
            menu_item.setdefault('selection_required', False)
            menu_item.setdefault('entity_types', [None])
            menu_item.setdefault('rich', {})
    
    # Create/Update.
    for url_or_entrypoint, spec in sorted(specs.iteritems()):

        if spec['is_sgaction']:
            url = url_base = 'sgaction:' + url_or_entrypoint
        else:
            url = url_base = url_or_entrypoint

        rich = spec.pop('rich')
        if rich:

            # Stuff the rich specs into the URL.
            if spec['is_sgaction']:
                rich = dict((k[0], v if isinstance(v, basestring) else json.dumps(v)) for k, v in rich.iteritems())
                url += '/' + '&'.join('%s=%s' % (k, urllib.quote(v)) for k, v in rich.iteritems())

            # URLs need to use the formatting method.
            else:
                title = rich.pop('title', None) or spec['title']
                if rich.get('heading'):
                    title = '%s / %s' % rich.pop('heading')
                if rich.get('icon'):
                    title = '%s [%s]' % rich.pop('icon')

        for entity_type in spec['entity_types']:
            
            # Get the new data.
            new_data = dict((name, spec[name]) for name in FIELD_NAMES if name in spec)
            new_data['entity_type'] = entity_type
            new_data['url'] = url
            
            # Get the old data.
            if url_base in existing:
                matches = [x for x in existing[url_base] if x['entity_type'] == entity_type]
                old_data = matches[0] if matches else {}
            else:
                old_data = {}
                        
            # Create.
            if not old_data:
                print 'Create %s / %s' % (url_or_entrypoint, entity_type)
                if not opts.dry_run:
                    sg.create('ActionMenuItem', new_data)
            
            # Update?
            else:
                id_ = old_data.pop('id')
                del old_data['type']
                if new_data != old_data or opts.force:
                    print 'Update %s / %s' % (url_or_entrypoint, entity_type)
                    if not opts.dry_run:
                        sg.update('ActionMenuItem', id_, new_data)
                else:
                    print 'Ignore %s / %s' % (url_or_entrypoint, entity_type)


if __name__ == '__main__':
    main()