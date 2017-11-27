event_name = self.request.get('txtEventName')
address = self.request.get('txtAddress')
txt_arrival_time = self.request.get('eventstart')
txt_stop_time = self.request.get('eventend')
transit_mode = self.request.get('travel')


jsonfile= json.dump()

call event_manaement_api