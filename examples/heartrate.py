# Standard modules
from random import randint  # for Random Heartrate
import dbus
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

# Bluezero modules
from bluezero import constants
from bluezero import adapter
from bluezero import advertisement
from bluezero import localGATT
from bluezero import GATT

# constants
HR_UUID = '0000180d-0000-1000-8000-00805f9b34fb'
HR_MSRMT_UUID = '00002a37-0000-1000-8000-00805f9b34fb'
NOTIFY_TIMEOUT = 1500


class HeartRateMeasurementChrc(localGATT.Characteristic):
    def __init__(self, service):
        localGATT.Characteristic.__init__(self,
                                          1,
                                          HR_MSRMT_UUID,
                                          service,
                                          [randint(90, 130)],
                                          False,
                                          ['read', 'notify'])

    def heartrate_calc(self):
        hr = randint(90, 130)
        value = []
        value.append(dbus.Byte(0x06))
        value.append(dbus.Byte(hr))

        self.props[constants.GATT_CHRC_IFACE]['Value'] = hr

        self.PropertiesChanged(constants.GATT_CHRC_IFACE, {'Value': value }, [])
        print('Value: ' + str(hr))
        return self.props[constants.GATT_CHRC_IFACE]['Notifying']

    def _update_value(self):
        if not self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            return

        print('Starting timer event')
        GObject.timeout_add(NOTIFY_TIMEOUT, self.heartrate_calc)

    def ReadValue(self, options):
        hr = randint(90, 130)
        value = []
        value.append(dbus.Byte(0x06))
        value.append(dbus.Byte(hr))
        self.props[constants.GATT_CHRC_IFACE]['Value'] = hr
        return value

    def StartNotify(self):
        if self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            print('Already notifying, nothing to do')
            return
        print('Notifying on')
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = True
        self._update_value()

    def StopNotify(self):
        if not self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            print('Not notifying, nothing to do')
            return

        print('Notifying off')
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = False
        self._update_value()


class ble:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.app = localGATT.Application()
        self.srv = localGATT.Service(1, HR_UUID, True)  # HR_UUID = '0000180d-0000-1000-8000-00805f9b34fb'

        self.charc = HeartRateMeasurementChrc(self.srv)

        self.charc.service = self.srv.path

        self.app.add_managed_object(self.srv)
        self.app.add_managed_object(self.charc)

        self.srv_mng = GATT.GattManager(adapter.list_adapters()[0])
        self.srv_mng.register_application(self.app, {})

        self.dongle = adapter.Adapter(adapter.list_adapters()[0])
        advert = advertisement.Advertisement(1, 'peripheral','HeartRate')
#        advert.appearance = [0x0341]  # Actually will give Error: Failed to register advertisement: org.bluez.Error.Failed: Failed to register advertisement
        advert.service_UUIDs = [HR_UUID]


        if not self.dongle.powered:
            self.dongle.powered = True
        ad_manager = advertisement.AdvertisingManager(self.dongle.address)
        ad_manager.register_advertisement(advert, {})

    def add_call_back(self, callback):
        self.charc.PropertiesChanged = callback

    def start_bt(self):
        # self.light.StartNotify()
        self.app.start()

#############################################################################
if __name__ == '__main__':
    print('Heartrate Example')

    hr_example = ble()
    hr_example.start_bt()
