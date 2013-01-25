#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop
from dbus.exceptions import DBusException

class SpotifyNotifier(object):

	def __init__(self):
		bus_loop = DBusGMainLoop(set_as_default=True)
		self.bus = dbus.SessionBus(mainloop=bus_loop)
		self.kmix = self.bus.get_object('org.kde.kmix', '/kmix/KMixWindow/actions/mute')
		self.muted = False
		loop = gobject.MainLoop()

		try: 
			self.props_changed_listener()
		except DBusException, e:
			if not ('org.mpris.MediaPlayer2.spotify '
					'was not provided') in e.get_dbus_message():
				raise
		self.session_bus = self.bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
		self.session_bus.connect_to_signal('NameOwnerChanged', self.handle_name_owner_changed, arg0='org.mpris.MediaPlayer2.spotify')

		loop.run()

	def toggleMute(self):
		self.kmix.get_dbus_method('trigger', 'org.qtproject.Qt.QAction')()
		if self.muted:
			self.muted = False
		else:
			self.muted = True
	

	def props_changed_listener(self):
		'''Hook up callback to PropertiesChanged event.'''
		self.spotify = self.bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
		self.spotify.connect_to_signal('PropertiesChanged', self.handle_properties_changed)

	def handle_name_owner_changed(self, name, older_owner, new_owner):
		'''Introspect the NameOwnerChanged signal to work out if spotify has started.'''
		if name == "org.mpris.MediaPlayer2.spotify":
			if new_owner:
				# spotify has been launched - hook it up.
				self.props_changed_listener()
			else:
				self.spotify = None

	def handle_properties_changed(self, interface, changed_props, invalidated_props):
		'''Handle track changes.'''
		metadata = changed_props.get("Metadata", {})
		if metadata:
			album = metadata.get("xesam:album") #dbus.String is a subtype of unicode
			print album
			if album.startswith('spotify') or 'http' in album:
				if not self.muted:
					self.toggleMute()
			else:
				if self.muted:
					self.toggleMute()

if __name__ == "__main__":
	SpotifyNotifier()
