import optparse
from pprint import pprint
import sys

import yaml
    
from shotgun.ks_shotgun import connect


FIELD_NAMES = ('id', 'title', 'list_order', 'entity_type', 'selection_required', 'url')


def main():
    
    optparser = optparse.OptionParser()
    optparser.add_option('-n', '--dry-run', action="store_true", dest="dry_run")
    optparser.add_option('-l', '--list', action="store_true", dest="list")
    optparser.add_option('-d', '--delete', action="store_true", dest="delete")    
    opts, args = optparser.parse_args()
    
    sg = connect()
    
    # Find and collapse existing.
    existing = {}
    individuals = sg.find('ActionMenuItem', [('url', 'starts_with', 'sgaction:')], FIELD_NAMES)
    for menu_item in individuals:
        existing.setdefault(menu_item['url'], []).append(menu_item)
    
    # List the existing menu items.
    if opts.list:
        for menu_items in sorted(existing.itervalues(), key=lambda x: (x[0]['list_order'], x[0]['title'])):
            print menu_items[0]['url']
            print '\ttitle: %s' % menu_items[0]['title']
            print '\tlist_order: %s' % menu_items[0]['list_order']
            print '\tentity_types:', ', '.join(str(x['entity_type']) for x in menu_items)
            print '\tids:', ', '.join(str(x['id']) for x in menu_items)
            print '\tselection_required: %s' % menu_items[0]['selection_required']
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
            if menu_item['entrypoint'] in specs:
                print 'WARNING: collision on', menu_item['entrypoint']
            specs[menu_item['entrypoint']] = menu_item
            menu_item.setdefault('title', menu_item['entrypoint'])
            menu_item.setdefault('list_order', None)
            menu_item.setdefault('selection_required', False)
            menu_item.setdefault('entity_types', [None])
    
    # Create/Update.
    for entrypoint, spec in sorted(specs.iteritems()):
        url = 'sgaction:' + entrypoint
        
        for entity_type in spec['entity_types']:
            
            # Get the new data.
            new_data = dict((name, spec[name]) for name in FIELD_NAMES if name in spec)
            new_data['entity_type'] = entity_type
            new_data['url'] = url
            
            # Get the old data.
            if url in existing:
                matches = [x for x in existing[url] if x['entity_type'] == entity_type]
                old_data = matches[0] if matches else {}
            else:
                old_data = {}
                        
            # Create.
            if not old_data:
                print 'Create %s / %s' % (entrypoint, entity_type)
                if not opts.dry_run:
                    sg.create('ActionMenuItem', new_data)
            
            # Update?
            else:
                id_ = old_data.pop('id')
                del old_data['type']
                if new_data != old_data:
                    print 'Update %s / %s' % (entrypoint, entity_type)
                    if not opts.dry_run:
                        sg.update('ActionMenuItem', id_, new_data)
                else:
                    print 'Ignore %s / %s' % (entrypoint, entity_type)


if __name__ == '__main__':
    main()