#!/usr/bin/env python2.5

import pango
import cairo
import gtk
import hildondesktop
import hildon
import gconf
import gobject
import time
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import sys
from PyICU import SimpleDateFormat, Locale, TimeZone

class MulticalDatePlugin(hildondesktop.HomePluginItem):
    def __init__(self):
        hildondesktop.HomePluginItem.__init__(self)
        self.set_settings(True)
        self.connect("show-settings", self.show_settings)
        self.gconfpath = '/apps/multical-date-widget';
        self.set_size_request(180,166)
        self.label = gtk.Label()
        self.label.set_justify(gtk.JUSTIFY_CENTER);
        self.label.show_all()
        self.add(self.label)
        self.update_timer = None
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        bus.add_signal_receiver(self.update_calendar,
            dbus_interface="com.nokia.alarmd",
            signal_name='time_change_ind',
            path='/com/nokia/alarmd')

    def do_expose_event(self, event):
        cr = self.window.cairo_create()
        cr.set_source_surface(cairo.ImageSurface.create_from_png('/opt/multical-date-widget/calendar.png'))
        cr.paint()
        hildondesktop.HomePluginItem.do_expose_event(self, event)

    def do_realize(self):
        self.widget_id = self.get_applet_id()
        conf_client = gconf.client_get_default()
        conf_client.add_dir(self.gconfpath, gconf.CLIENT_PRELOAD_NONE)
        self.locale = conf_client.get_string(self.gconfpath + "/" + self.widget_id + ".locale")
        self.calendar = conf_client.get_string(self.gconfpath + "/" + self.widget_id + ".calendar")
        if self.locale == None:
            self.locale = 'fa_IR'
        if self.calendar == None:
            self.calendar = 'Persian'
        self.update_calendar()
        self.set_colormap(self.get_screen().get_rgba_colormap())
        self.set_app_paintable(True)
        hildondesktop.HomePluginItem.do_realize(self)        
	
    def update_calendar(self):
        if (self.update_timer):
            gobject.source_remove(self.update_timer)
        self.update_timer = gobject.timeout_add(int(86400 - (time.time() - time.mktime(time.strptime(time.strftime('%Y%m%d'), '%Y%m%d')))) * 1000, self.update_calendar)
        df = SimpleDateFormat('yyyy-MMMM-d', Locale(self.locale + '@calendar=' + self.calendar))
        df.setTimeZone(TimeZone.getGMT());
        date = df.format(time.time() - time.timezone + (3600 if time.daylight else 0)).encode('utf-8').split('-')
        self.label.set_markup('<span rise="-20000" foreground="white" font_desc="mitra bold 16">' + date[0] + '</span>\n' +
		    '<span foreground="black" rise="-50000" font_desc="mitra bold 38">' + date[2] + '</span>\n' +
		    '<span foreground="black" font_desc="mitra bold 16">' + date[1] + '</span>')

    def show_settings(self, widget):
        dialog = gtk.Dialog("Settings" , None, gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR)
        dialog.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        
        main_vbox = gtk.VBox()
      
        ts = hildon.TouchSelector()
        ts.add(main_vbox)
        
        locales = []
        locales_dict = {}
        for code, locale in Locale.getAvailableLocales().iteritems():
            locales.append(locale.getDisplayName())
            locales_dict[code] = locale.getDisplayName()
        locales.sort()
        locale_btn = hildon.PickerButton(gtk.HILDON_SIZE_FULLSCREEN_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT, hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
        locale_btn.set_text("Language:", '-')
        locale_select = hildon.TouchSelector(text=True)        
        for locale in locales:
            locale_select.append_text(locale)
        locale_select.set_active(0, locales.index(Locale(self.locale).getDisplayName()))
        locale_btn.set_selector(locale_select)
        locale_btn.show_all()

        calendar_btn = hildon.PickerButton(gtk.HILDON_SIZE_FULLSCREEN_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT, hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
        calendar_btn.set_text("Calendar:", "-")
        calendar_select = hildon.TouchSelector(text=True)
        calendars = ["Buddhist", "Chinese", "Coptic", "Ethiopic", "Gregorian", "Hebrew",
                     "Indian", "Islamic", "Islamic-Civil", "Japanese", "Persian", "Taiwan"]
        for calendar in calendars:
            calendar_select.append_text(calendar)
        calendar_select.set_active(0, calendars.index(self.calendar))
        calendar_btn.set_selector(calendar_select)
        calendar_btn.show_all()

        main_vbox.pack_start(locale_btn)
        main_vbox.pack_start(calendar_btn)

        dialog.vbox.add(ts)
        dialog.show_all()
        response = dialog.run()
     
        if response == gtk.RESPONSE_OK:
            self.locale = [k for k, v in locales_dict.iteritems() if v == locale_select.get_current_text()][0]
            self.calendar = calendar_select.get_current_text()
            conf_client = gconf.client_get_default()
            conf_client.add_dir(self.gconfpath, gconf.CLIENT_PRELOAD_NONE)
            conf_client.set_string(self.gconfpath + "/" + self.widget_id + ".locale", self.locale)
            conf_client.set_string(self.gconfpath + "/" + self.widget_id + ".calendar", self.calendar)
            self.update_calendar()
        dialog.destroy()

hd_plugin_type = MulticalDatePlugin

# The code below is just for testing purposes.
# It allows to run the widget as a standalone process.
if __name__ == "__main__":
    import gobject
    gobject.type_register(hd_plugin_type)
    obj = gobject.new(hd_plugin_type, plugin_id="plugin_id")
    obj.show_all()
    gtk.main()
