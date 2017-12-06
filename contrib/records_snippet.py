import enigma
import pprint
import NavigationInstance
#pprint.pprint(dir(enigma.iServiceInformation))
from enigma import iServiceInformation

nin = NavigationInstance.instance
#print dir(nin)
print dir(nin.RecordTimer)

pprint.pprint(nin.RecordTimer.timer_list)

print dir(nin.RecordTimer.timer_list[0])
# ['PVRFilename', 'StateEnded', 'StatePrepared', 'StateRunning', 'StateWaiting', 'Timer', 'TryQuitMainloop', '_RecordTimerEntry__record_service', 
# 'abort', 'activate', 'addOneDay', 'afterEvent', 'autoincrease', 'autoincreasetime', 'backoff', 'begin', 'calculateFilename', 
# 'cancelled', 'delayed_zap', 'descramble', 'description', 'dirname', 'dirnameHadToFallback', 'disable', 'disabled', 'do_backoff', 'dontSave', 
# 'eit', 'enable', 'end', 'failureCB', 'first_try_prepare', 'getNextActivation', 'gotRecordEvent', 'isRunning', 'is_timeshift', 'is_transformed_timeshift', 
# 'justplay', 'justremind', 'log', 'log_entries', 'name', 'notify_t', 'prepare_time', 'processRepeated', 'pvrConvert', 'receiveRecordEvents', 
# 'record_ecm', 'record_service', 'repeated', 'repeatedbegindate', 'resetRepeated', 'resetState', 'sendStandbyNotification',
# 'sendTryQuitMainloopNotification', 'service_ref', 'setAutoincreaseEnd', 'setRecordService', 'setRepeated', 'shouldSkip', 'shutdown', 'shutdown_t', 
# 'standby_t', 'start_prepare', 'state', 'staticGotRecordEvent', 'stopTryQuitMainloop', 'tags', 'timeChanged', 'timer', 'tryPrepare', 
# 'virtual_video_dir', 'wakeup_t', 'zapbeforerecord', 'zaptoReminderCB']
first = nin.RecordTimer.timer_list[0]
print "EIT:"
print first.eit

# print "first.calculateFilename:"
# print repr(first.calculateFilename())
print first.begin
print first.disabled
print first.name