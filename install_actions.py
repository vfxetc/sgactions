from shotgun.ks_shotgun import connect

sg = connect()

source = '''

console.log('this', this);
console.log('docment', document);
console.log('document.location', document.location);
console.log('window', window);
    
if(!window.jQuery){
    var s = document.createElement('script');
    s.src = '//ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js';
    document.getElementsByTagName('head')[0].appendChild(s);
 
    var z = setInterval(function(){
        if(window.jQuery){
            $j = jQuery.noConflict();
            alert('jQuery loaded!');
            window.clearInterval(z);
        }
    },100);
}

'''

# sg.update('ActionMenuItem', 1, dict(url="javascript:%s;//" % source))
# sg.update('ActionMenuItem', 1, dict(title="SGAction Kwargs", url="sgaction:sgactions.dispatch:test_kwargs"))
sg.update('ActionMenuItem', 1, dict(title="[DEV] SGAction Environ", url="sgaction:sgactions.dispatch:test_environ"))
