#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import gobject
from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
from dbus.exceptions import DBusException

class SpotifyNotifier(object):

	def __init__(self):
		bus_loop = DBusGMainLoop(set_as_default=True)
		self.bus = dbus.SessionBus(mainloop=bus_loop)
		self._dbus_mixer_prop = None
		self._dbus_toggleMute = None
		loop = gobject.MainLoop()

		try: 
			self.props_changed_listener()
		except DBusException, e:
			if not ('org.mpris.MediaPlayer2.spotify '
					'was not provided') in e.get_dbus_message():
				raise
		self.session_bus = self.bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
		self.session_bus.connect_to_signal('NameOwnerChanged', self.handle_name_owner_changed, arg0='org.mpris.MediaPlayer2.spotify')
		self._dbug_find_spotify_control()

		try:
			loop.run()
		except KeyboardInterrupt:
			print 'You will hear your ad\'s again - good bye!'

	def isMuted(self):
		return self._dbus_mixer_prop.Get('', 'mute')

	def toggleMute(self):
		self._dbus_toggleMute()

	def dbus_get_kmix_property(self, obj_path, prop):
		return self.bus.get_object('org.kde.kmix', obj_path).Get('', prop, dbus_interface='org.freedesktop.DBus.Properties')

	def _dbug_find_spotify_control(self):
		'''find the spotify control in kmix'''
		for mixer in self.dbus_get_kmix_property('/Mixers', 'mixers'):
			for control in self.dbus_get_kmix_property(mixer, 'controls'):
				if 'spotify' in self.dbus_get_kmix_property(control, 'readableName').lower():
					print 'found control: "%s"' % control
					self._dbus_toggleMute = self.bus.get_object('org.kde.kmix', control).get_dbus_method('toggleMute', 'org.kde.KMix.Control')
					self._dbus_mixer_prop = dbus.Interface(self.bus.get_object('org.kde.kmix', control), dbus_interface='org.freedesktop.DBus.Properties')
					return
		print 'ERROR: spotify control not found in kmix...'

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
			album = metadata.get("xesam:album").lower() #dbus.String is a subtype of unicode
			if album.startswith('spotify') or 'http' in album:
				print 'Possible ad: "%s"' % album
				if not self.isMuted():
					self.toggleMute()
			else:
				print 'Not an ad: "%s"' % album
				if self.isMuted():
					# last track was an add, sleep one second, than unmute
					sleep(1)
					self.toggleMute()

if __name__ == "__main__":
	SpotifyNotifier()
