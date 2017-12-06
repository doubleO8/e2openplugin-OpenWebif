import enigma
import pprint
#print globals().keys()
#pprint.pprint(dir(self.session.nav.getCurrentService()))

keys = [
 'audioChannel',
 'audioDelay',
 'audioTracks',
 'cueSheet',
 'frontendInfo',
 'getPtrString',
 'info',
 'keys',
 #'pause',
 'rdsDecoder',
 #'seek',
 #'setQpipMode',
 #'setTarget',
 #'start',
 #'stop',
 #'stream',
 #'streamed',
 'subServices',
 'subtitle',
 #'this',
 #'thisown',
 #'timeshift'
 ]

cs = self.session.nav.getCurrentService()
for key in keys:
    result = None
    attribute = getattr(cs, key, None)
    is_callable = callable(attribute)
    if is_callable:
        result = attribute()
    else:
        result = attribute
    print("{!s}{:s}: {!r}".format(key, (is_callable and " [C]" or ""), result))